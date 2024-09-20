import re

import iproute4mac.libc as libc
import iproute4mac.utils as utils

from iproute4mac.data import _Item, _Items, dict_format, find_item
from iproute4mac.prefix import Prefix


_IFCONFIG = "ifconfig"
_IFCONFIG_OPTS = ["-L", "-m", "-v"]

_SYSCTL_RXQLEN = "net.link.generic.system.rcvq_maxlen"
_SYSCTL_TXQLEN = "net.link.generic.system.sndq_maxlen"
_TXQLEN = libc.sysctl(_SYSCTL_TXQLEN)

# nu <netinet6/nd6.h>
_ND6_INFINITE_LIFETIME = 0xFFFFFFFF

# map operstates
OPER_STATES = {"active": "UP", "inactive": "DOWN", "none": "UNKNOWN"}

# MAC address RegEx
LLSEG = "[0-9a-fA-F]{1,2}"
LLADDR = "(?:%s(?::%s){5})" % (LLSEG, LLSEG)

# IPv4 RegEx
IPV4SEG = "(?:25[0-5]|2[0-4][0-9]|1{0,1}[0-9]{1,2})"
IPV4ADDR = r"(?:%s(?:\.%s){0,3})" % (IPV4SEG, IPV4SEG)
IPV4MASK = "(?:0x)?(?:[0-9a-fA-F]){8}"

# IPv6 RegEx
IPV6SEG = "(?:[0-9a-fA-F]{1,4})"
IPV6GROUPS = (
    "::",
    "(?:%s:){1,7}:" % (IPV6SEG),
    ":(?::%s){1,7}" % (IPV6SEG),
    "(?:%s:){1,6}:%s" % (IPV6SEG, IPV6SEG),
    "%s:(?::%s){1,6}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,5}(?::%s){1,2}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,4}(?::%s){1,3}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,3}(?::%s){1,4}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,2}(?::%s){1,5}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){7,7}%s" % (IPV6SEG, IPV6SEG),
)
IPV6ADDR = "|".join([f"(?:{group})" for group in IPV6GROUPS[::-1]])
IPV6ADDR = f"(?:{IPV6ADDR})"

# ifconfig
IFNAME = r"(?:\w+\d+)"
NETIF = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"


# https://opensource.apple.com/source/network_cmds/network_cmds-606.40.2/ifconfig.tproj/ifconfig.c.auto.html


def run(*argv, fatal=True):
    if not argv:
        argv = _IFCONFIG_OPTS
    return utils.shell(_IFCONFIG, *argv, fatal=fatal)


def netmask_to_length(mask):
    return utils.bit_count(int(mask, 16))


class _reBase:
    __slots__ = ("_data",)

    def __init__(self, pattern, text):
        if not isinstance(pattern, re.Pattern):
            raise ValueError("pattern is not of {re.Pattern}")
        if not isinstance(text, str):
            raise ValueError("data is not of {str}")

    def expand_groupdict(self, data):
        res = {}
        for key, value in data.items():
            if key == "flags":
                value = value.split(",") if value else []
            res[key] = value
        return res

    @property
    def data(self):
        return self._data


class _reList(_reBase):
    """
    Input: re.Pattern, str
    Output: list(str) or list(dict)
    """

    def __init__(self, pattern, text):
        super().__init__(pattern, text)
        self._data = []
        for res in pattern.finditer(text):
            if res.groupdict():
                self._data.append(self.expand_groupdict(res.groupdict()))
            elif res.groups():
                self._data.extend(res.groups())
            else:
                self._data.append(res.group())


class _reDict(_reBase):
    """
    Input: re.Pattern, str
    Output: dict
    """

    def __init__(self, pattern, text):
        super().__init__(pattern, text)
        self._data = pattern.search(text)

    @property
    def data(self):
        return self.expand_groupdict(self.groupdict())

    def groupdict(self):
        return self._data.groupdict() if self._data else {}

    def groups(self):
        return self._data.groups() if self._data else None

    def group(self, *index):
        return self._data.group(*index) if self._data else None


class _reBridge(_reBase):
    _bridge = re.compile(
        r"\tConfiguration:\n"
        r"\t\s+id (?P<id>\S+) priority (?P<priority>\d+) hellotime (?P<hellotime>\d+) fwddelay (?P<fwddelay>\d+)\n"
        r"\t\s+maxage (?P<maxage>\d+) holdcnt (?P<holdcnt>\d+) proto (?P<proto>\w+) maxaddr (?P<maxaddr>\d+) timeout (?P<timeout>\d+)\n"
        r"\t\s+root id (?P<root_id>\S+) priority (?P<root_priority>\d+) ifcost (?P<root_cost>\d+) port (?P<root_port>\d+)\n"
        r"\t\s+ipfilter (?P<ipfilter>\w+) flags (?P<flag>0x[0-9a-fA-F]+)"
    )
    _member = re.compile(
        r"\tmember: (?P<interface>\w+) flags=(?P<flag>\w+)<(?P<flags>.*)>\n"
        r"\t\s+ifmaxaddr (?P<ifmaxaddr>\d+) port (?P<port>\d+) priority (?P<priority>\d+) path cost (?P<cost>\d+)\n"
        r"\t\s+hostfilter (?P<hostfilter>\d+) hw: (?P<hw>\S+) ip: (?P<ip>\S+)\n"
        r"(?:\t\s+checksum stats:\n(?P<checksum_stats>(?:.*\n)+))?"
    )

    def __init__(self, pattern, text):
        super().__init__(pattern, text)
        self._data = pattern.search(text)
        if self._data:
            text = self._data.group()
            self._data = {
                **_reDict(self._bridge, text).data,
                "member": _reList(self._member, text).data,
            }


class _reMedia(_reList):
    _media = re.compile(r"\t\t(?:media (?P<type>\S+)|<unknown type>)")
    _mediaopt = re.compile(r"mediaopt (\S+)")

    def __init__(self, pattern, text):
        super().__init__(pattern, text)
        for i, text in enumerate(self._data):
            self._data[i] = {
                "type": self._media.search(text).group(1),
                "opts": _reList(self._mediaopt, text).data,
            }


class _reBond(_reList):
    _bond = re.compile(r"\tbond interfaces:(?P<bond> \w+(?: \w+)*)")
    _list = re.compile(r" (\S+)")

    def __init__(self, pattern, text):
        super().__init__(pattern, text)
        if text := _reDict(self._bond, text).group("bond"):
            self._data = _reList(self._list, text).data


class _IfconfigBase(_Item):
    _name = None
    _link = None
    _OPTIONAL_FIELDS = {
        "eflags": None,
        "xflags": None,
        "options": None,
        "capabilities": None,
        "hwassist": None,
        "promiscuity": None,
        "min_mtu": None,
        "max_mtu": None,
        "linkinfo": None,
        "num_tx_queues": None,
        "num_rx_queues": None,
        "gso_max_size": None,
        "gso_max_segs": None,
    }

    @property
    def name(self):
        return self._name

    @property
    def link(self):
        return self._link

    @link.setter
    def link(self, link):
        if not isinstance(link, _IfconfigBase):
            raise ValueError(f"link must by of {_IfconfigBase}")
        self._link = link


class _Ifconfig(_IfconfigBase):
    _name_data = re.compile(r"(?P<interface>\w+): (?P<data>(?:.*)(?:\n\t.*)+)")
    _interface = re.compile(
        r"flags=(?P<flag>\w+)<(?P<flags>.*)> mtu (?P<mtu>\d+)?(?: rtref (?P<rtref>\d+))? index (?P<index>\d+)"
    )
    _eflags = re.compile(r"\teflags=(?P<flag>\w+)<(?P<flags>.*)>")
    _xflags = re.compile(r"\txflags=(?P<flag>\w+)<(?P<flags>.*)>")
    _options = re.compile(r"\toptions=(?P<flag>\w+)<(?P<flags>.*)>")
    _capabilities = re.compile(r"\tcapabilities=(?P<flag>\w+)<(?P<flags>.*)>")
    _hwassist = re.compile(r"\thwassist=(?P<flag>\w+)<(?P<flags>.*)>")
    _ether = re.compile(r"\tether (?P<ether>\S+)")
    _bridge = re.compile(r"\tConfiguration:\n(?:\t\t.*\n)+(?:\tmember: .*\n(?:\t\s+.*\n)+)*")
    _peer = re.compile(r"\s+peer: (?P<peer>\w+)")
    _tunnel = re.compile(r"\s+tunnel inet (?P<src>\S+) --> (?P<dst>\S+)")
    _address = re.compile(
        r"\t(?P<family>inet|inet6) (?P<address>[^/^%^ ]+)(?:%(?P<net>\w+))?"
        r"(?: --> (?P<peer>[^/^%^ ]+)(?:%\w+)?)?"
        r"(?: prefixlen (?P<prefixlen>\d+))?"
        r"(?: netmask 0x(?P<netmask>[0-9a-fA-F]{8}))?"
        r"(?: broadcast (?P<broadcast>\S+))?"
        r"(?: (?P<autoconf>autoconf))?"
        r"(?: (?P<secured>secured))?"
        r"(?: pltime (?P<pltime>\d+))?"
        r"(?: vltime (?P<vltime>\d+))?"
        r"(?: scopeid (?P<scopeid>\S+))?"
    )
    _vlan = re.compile(r"\s+vlan: (?P<vlanid>\d+) parent interface: (?P<parent>\<none\>|\S+)")
    _netif = re.compile(r"\tnetif: (?P<netif>\S+)")
    _flowswitch = re.compile(r"\tflowswitch: (?P<flowswitch>\S+)")
    _nd6_options = re.compile(r"\tnd6 options=(?P<flag>\w+)<(?P<flags>.*)>")
    _media = re.compile(r"\tmedia: (?P<media>.+)")
    _status = re.compile(r"\tstatus: (?P<status>\w+)")
    _supported_media = re.compile(r"\t\t(?:media .*|<unknown type>)")
    _bond = re.compile(r"\tbond interfaces:(?: \w+)+")
    _generation_id = re.compile(r"\tgeneration id: (?P<generation_id>\d+)")
    _type = re.compile(r"\ttype: (?P<type>.*)")
    _agent = re.compile(
        r'\tagent domain:(?P<domain>[\w\.]+) type:(?P<type>\w+) flags:(?P<flag>0x[0-9a-fA-F]+) desc:"(?P<desc>.*)"'
    )
    _link_quality = re.compile(r"\tlink quality: (?P<quality>\d+) \((?P<desc>\w+)\)")
    _state_availability = re.compile(
        r"\tstate availability: (?P<availability>\d+) \((?P<desc>\w+)\)"
    )
    _scheduler = re.compile(r"\tscheduler: (?P<type>\w+)(?: (?P<desc>.*))?")
    _effective_interface = re.compile(r"\teffective interface: (?P<effective_interface>\w+)")
    _link_rate = re.compile(r"\tlink rate: (?P<rate>[\d\.]+) (?P<rate_um>\w+)")
    _uplink_rate = re.compile(
        r"\tuplink rate: (?P<eff>[\d\.]+) (?P<eff_um>\w+) \[eff\] / (?P<max>[\d\.]+) (?P<max_um>\w+)"
    )
    _downlink_rate = re.compile(
        r"\tdownlink rate: (?P<eff>[\d\.]+) (?P<eff_um>\w+) \[eff\] / (?P<max>[\d\.]+) (?P<max_um>\w+)"
    )
    _timestamp = re.compile(r"\ttimestamp: (?P<timestamp>\w+)")
    _desc = re.compile(r"\tdesc: (?P<desc>\S+)")
    _unaligned_pkts = re.compile(r"\tunaligned pkts: (?P<unaligned_pkts>\d+)")
    _qosmarking = re.compile(r"\tqosmarking enabled: (?P<enabled>\w+) mode: (?P<mode>\w+)")
    _low_power_mode = re.compile(r"\tlow power mode: (?P<low_power_mode>\w+)")
    _mpklog = re.compile(r"\tmulti layer packet logging \(mpklog\): (?P<mpklog>\w+)")
    _routermode4 = re.compile(r"\troutermode4: (?P<routermode4>\w+)")
    _routermode6 = re.compile(r"\troutermode6: (?P<routermode6>\w+)")

    def __init__(self, text):
        (self._name, text) = _reDict(self._name_data, text).groups()

        self._data = {
            "interface": self._name,
            **_reDict(self._interface, text).data,
            "eflags": _reDict(self._eflags, text).data,
            "xflags": _reDict(self._xflags, text).data,
            "options": _reDict(self._options, text).data,
            "capabilities": _reDict(self._capabilities, text).data,
            "hwassist": _reDict(self._hwassist, text).data,
            **_reDict(self._ether, text).data,
            "broadcast": None,
            "bridge": _reBridge(self._bridge, text).data,
            **_reDict(self._peer, text).data,
            "tunnel": _reDict(self._tunnel, text).data,
            "address": _reList(self._address, text).data,
            "vlan": _reDict(self._vlan, text).data,
            **_reDict(self._netif, text).data,
            **_reDict(self._flowswitch, text).data,
            "nd6_options": _reDict(self._nd6_options, text).data,
            **_reDict(self._media, text).data,
            **_reDict(self._status, text).data,
            "supported_media": _reMedia(self._supported_media, text).data,
            "bond": _reBond(self._bond, text).data,
            **_reDict(self._generation_id, text).data,
            **_reDict(self._type, text).data,
            "link_type": "unknown",
            "agent": _reList(self._agent, text).data,
            "link_quality": _reDict(self._link_quality, text).data,
            "state_availability": _reDict(self._state_availability, text).data,
            "scheduler": _reDict(self._scheduler, text).data,
            **_reDict(self._effective_interface, text).data,
            "link_rate": _reDict(self._link_rate, text).data,
            "uplink_rate": _reDict(self._uplink_rate, text).data,
            "downlink_rate": _reDict(self._downlink_rate, text).data,
            **_reDict(self._timestamp, text).data,
            **_reDict(self._desc, text).data,
            **_reDict(self._unaligned_pkts, text).data,
            "qosmarking": _reDict(self._qosmarking, text).data,
            **_reDict(self._low_power_mode, text).data,
            **_reDict(self._mpklog, text).data,
            **_reDict(self._routermode4, text).data,
            **_reDict(self._routermode6, text).data,
        }

        if self._data.get("ether"):
            self._data["link_type"] = "ether"
            self._data["broadcast"] = "ff:ff:ff:ff:ff:ff"
        elif "LOOPBACK" in self._data["flags"]:
            self._data["link_type"] = "loopback"
            self._data["ether"] = "00:00:00:00:00:00"
            self._data["broadcast"] = "00:00:00:00:00:00"
        elif "POINTOPOINT" in self._data["flags"] and self._data.get("tunnel"):
            self._data["link_type"] = "ipip"
        else:
            self._data["link_type"] = "none"

    def str(self, details=True):
        data = self.data
        res = f"{self._name}: flags={data['flag']}<{','.join(data['flags'])}>"
        res += dict_format(data, " mtu {}", "mtu")
        res += dict_format(data, " rtref {}", "rtref")
        res += f" index {data['index']}\n"
        for flags in ["eflags", "xflags", "options", "capabilities", "hwassist"]:
            if data.get(flags):
                res += f"\t{flags}={data[flags]['flag']}<{','.join(data[flags]['flags'])}>\n"
        if self._data["link_type"] != "loopback":
            res += dict_format(data, "\tether {}\n", "ether")
        if self.name.startswith("feth"):
            res += dict_format(data, "\tpeer: {}\n", "peer", default="<none>")
        if data.get("tunnel"):
            res += f"\ttunnel inet {data['tunnel']['src']} --> {data['tunnel']['dst']}\n"
        for addr in data.get("address", []):
            res += f"\t{addr['family']} {addr['address']}"
            res += dict_format(addr, "%{}", "net")
            res += dict_format(addr, " --> {}", "peer")
            if addr.get("netmask"):
                res += dict_format(addr, " netmask 0x{}", "netmask")
            else:
                res += dict_format(addr, " prefixlen {}", "prefixlen")
            res += dict_format(addr, " broadcast {}", "broadcast")
            res += dict_format(addr, " {}", "autoconf")
            res += dict_format(addr, " {}", "secured")
            res += dict_format(addr, " pltime {}", "pltime")
            res += dict_format(addr, " vltime {}", "vltime")
            res += dict_format(addr, " scopeid {}", "scopeid")
            res += "\n" if addr["family"] == "inet" else " \n"
        if data.get("bridge"):
            bridge = data["bridge"]
            res += "\tConfiguration:\n"
            res += f"\t\tid {bridge['id']} priority {bridge['priority']} hellotime {bridge['hellotime']} fwddelay {bridge['fwddelay']}\n"
            res += f"\t\tmaxage {bridge['maxage']} holdcnt {bridge['holdcnt']} proto {bridge['proto']} maxaddr {bridge['maxaddr']} timeout {bridge['timeout']}\n"
            res += f"\t\troot id {bridge['root_id']} priority {bridge['root_priority']} ifcost {bridge['root_cost']} port {bridge['root_port']}\n"
            res += f"\t\tipfilter {bridge['ipfilter']} flags {bridge['flag']}\n"
            for member in bridge.get("member", []):
                res += f"\tmember: {member['interface']} flags={member['flag']}<{','.join(member['flags'])}>\n"
                res += f"\t        ifmaxaddr {member['ifmaxaddr']} port {member['port']} priority {member['priority']} path cost {member['cost']}\n"
                res += f"\t        hostfilter {member['hostfilter']} hw: {member['hw']} ip: {member['ip']}\n"
                res += dict_format(member, "\t\tchecksum stats:\n{}", "checksum_stats")
            # res += "\tAddress cache:\n"
        res += dict_format(
            data.get("vlan"), "\tvlan: {} parent interface: {}\n", "vlanid", "parent"
        )
        res += dict_format(data, "\tnetif: {}\n", "netif")
        res += dict_format(data, "\tflowswitch: {}\n", "flowswitch")
        if data.get("nd6_options"):
            res += f"\tnd6 options={data['nd6_options']['flag']}<{','.join(data['nd6_options']['flags'])}>\n"
        res += dict_format(data, "\tmedia: {}\n", "media")
        res += dict_format(data, "\tstatus: {}\n", "status")
        if data.get("media"):
            res += "\tsupported media:\n"
            for media in data.get("supported_media", []):
                if media["type"]:
                    res += dict_format(media, "\t\tmedia {}", "type")
                    for opt in media["opts"]:
                        res += f" mediaopt {opt}"
                else:
                    res += "\t\t<unknown type>"
                res += "\n"
        if self._name.startswith("bond"):
            members = " ".join(data["bond"]) if data["bond"] else "<none>"
            res += f"\tbond interfaces: {members}\n"
        res += dict_format(data, "\tgeneration id: {}\n", "generation_id")
        res += dict_format(data, "\ttype: {}\n", "type")
        for agent in data.get("agent", []):
            res += dict_format(
                agent,
                '\tagent domain:{} type:{} flags:{} desc:"{}"\n',
                "domain",
                "type",
                "flag",
                "desc",
            )
        res += dict_format(data.get("link_quality"), "\tlink quality: {} ({})\n", "quality", "desc")
        res += dict_format(
            data.get("state_availability"),
            "\tstate availability: {} ({})\n",
            "availability",
            "desc",
        )
        res += dict_format(data.get("scheduler"), "\tscheduler: {} {}\n", "type", "desc")
        res += dict_format(data, "\teffective interface: {}\n", "effective_interface")
        res += dict_format(data.get("link_rate"), "\tlink rate: {} {}\n", "rate", "rate_um")
        res += dict_format(
            data.get("uplink_rate"),
            "\tuplink rate: {} {} [eff] / {} {}\n",
            "eff",
            "eff_um",
            "max",
            "max_um",
        )
        res += dict_format(
            data.get("downlink_rate"),
            "\tdownlink rate: {} {} [eff] / {} {} [max]\n",
            "eff",
            "eff_um",
            "max",
            "max_um",
        )
        res += dict_format(data, "\ttimestamp: {}\n", "timestamp")
        res += dict_format(data, "\tdesc: {}\n", "desc")
        res += dict_format(data, "\tunaligned pkts: {}\n", "unaligned_pkts")
        res += dict_format(
            data.get("qosmarking"),
            "\tqosmarking enabled: {} mode: {}\n",
            "enabled",
            "mode",
        )
        res += dict_format(data, "\tlow power mode: {}\n", "low_power_mode")
        res += dict_format(data, "\tmulti layer packet logging (mpklog): {}\n", "mpklog")
        res += dict_format(data, "\troutermode4: {}\n", "routermode4")
        res += dict_format(data, "\troutermode6: {}\n", "routermode6")
        return res.rstrip()


class _IpAddress(_IfconfigBase):
    __slots__ = ("_ifconfig",)

    def __init__(self, text):
        self._ifconfig = _Ifconfig(text)
        self._name = self._ifconfig._name
        self._data = {
            "ifindex": self._ifconfig["index"],
            "link": self._get_link(),
            "ifname": self._name,
            "flags": self._ifconfig["flags"],
            "eflags": self._ifconfig.get("eflags", {}).get("flags"),
            "xflags": self._ifconfig.get("xflags", {}).get("flags"),
            "options": self._ifconfig.get("options", {}).get("flags"),
            "capabilities": self._ifconfig.get("capabilities", {}).get("flags"),
            "hwassist": self._ifconfig.get("hwassist", {}).get("flags"),
            "mtu": self._ifconfig["mtu"],
            # "qdisc": "noqueue",
            "master": None,  # async __update__ with self._get_master()
            "operstate": OPER_STATES[self._ifconfig.get("status", "none")],
            "group": "default",
            "txqlen": _TXQLEN,
            "link_type": self._ifconfig.get("link_type"),
            "address": self._ifconfig.get("ether"),
            "link_pointtopoint": True if "POINTOPOINT" in self._ifconfig["flags"] else None,
            "broadcast": self._ifconfig.get("broadcast"),
            # TODO:
            # "promiscuity": 0,
            # "min_mtu": 0,
            # "max_mtu": 0,
            "linkinfo": None,  # async __update__ with self._get_linkinfo()
            # TODO:
            # "num_tx_queues": 1,
            # "num_rx_queues": 1,
            # "gso_max_size": 65536,
            # "gso_max_segs": 65535,
            "addr_info": self._get_addr_info(),
        }
        if self._ifconfig.get("tunnel"):
            self._data["address"] = self._ifconfig["tunnel"]["src"]
            self._data["broadcast"] = self._ifconfig["tunnel"]["dst"]

    def __update__(self):
        self._data.update(
            {
                "master": self._get_master(),
                "linkinfo": self._get_linkinfo(),
            }
        )

    def _get_link(self):
        if self._ifconfig.get("peer"):
            return self._ifconfig["peer"]
        if self._ifconfig.get("vlan", {}).get("parent"):
            return self._ifconfig["vlan"]["parent"]
        return None

    def _get_master(self):
        return self.link.name if self.link else None

    def _get_info_kind(self):
        if utils.startwith(self._ifconfig["interface"], "bridge", "bond", "feth", "gif", "vlan"):
            return re.sub("[0-9]+", "", self._ifconfig["interface"])
        return None

    def _get_info_data(self):
        info_data = {}
        if self._ifconfig.get("vlan", {}).get("vlanid"):
            info_data.update(
                {"protocol": "802.1Q", "id": self._ifconfig["vlan"]["vlanid"], "flags": []}
            )
        if self._ifconfig.get("bridge"):
            info_data.update(
                {
                    "forward_delay": self._ifconfig["bridge"]["fwddelay"],
                    "hello_time": self._ifconfig["bridge"]["hellotime"],
                    "max_age": self._ifconfig["bridge"]["maxage"],
                    "ageing_time": self._ifconfig["bridge"]["timeout"],
                    # "stp_state": 0,
                    "priority": self._ifconfig["bridge"]["root_priority"],
                    # "vlan_filtering": 0,
                    # "vlan_protocol": "802.1Q",
                    "bridge_id": self._ifconfig["bridge"]["id"],
                    "root_id": self._ifconfig["bridge"]["root_id"],
                    "root_port": self._ifconfig["bridge"]["root_port"],
                    "root_path_cost": self._ifconfig["bridge"]["root_cost"],
                    # TODO:
                    # "topology_change": 0,
                    # "topology_change_detected": 0,
                    # "hello_timer": 0.00,
                    # "tcn_timer": 0.00,
                    # "topology_change_timer": 0.00,
                    # "gc_timer": 294.74,
                    # "vlan_default_pvid": 1,
                    # "vlan_stats_enabled": 0,
                    # "vlan_stats_per_port": 0,
                    # "group_fwd_mask": "0",
                    # "group_addr": "01:80:c2:00:00:00",
                    # "mcast_snooping": 1,
                    # "mcast_router": 1,
                    # "mcast_query_use_ifaddr": 0,
                    # "mcast_querier": 0,
                    # "mcast_hash_elasticity": 16,
                    # "mcast_hash_max": 4096,
                    # "mcast_last_member_cnt": 2,
                    # "mcast_startup_query_cnt": 2,
                    # "mcast_last_member_intvl": 100,
                    # "mcast_membership_intvl": 26000,
                    # "mcast_querier_intvl": 25500,
                    # "mcast_query_intvl": 12500,
                    # "mcast_query_response_intvl": 1000,
                    # "mcast_startup_query_intvl": 3124,
                    # "mcast_stats_enabled": 0,
                    # "mcast_igmp_version": 2,
                    # "mcast_mld_version": 1,
                    # "nf_call_iptables": 0,
                    # "nf_call_ip6tables": 0,
                    # "nf_call_arptables": 0,
                    "ipfilter": self._ifconfig["bridge"]["ipfilter"],
                }
            )
        return info_data if info_data else None

    def _get_info_slave_kind(self):
        if self.link:
            return self.link._get_info_kind()
        return None

    def _get_info_slave_data(self):
        if self.link:
            if self.link.name.startswith("bond"):
                # FIXME: where to find original hardawre lladdr?
                return {"perm_hwaddr": self._ifconfig["ether"]}
            if self.link.name.startswith("bridge"):
                bridge = self.link._ifconfig._data["bridge"]
                if member := next(
                    (member for member in bridge["member"] if member["interface"] == self._name),
                    None,
                ):
                    return {
                        "state": "forwarding",
                        "priority": int(member["priority"]),
                        "cost": int(member["cost"]),
                        # "hairpin": False,
                        # "guard": False,
                        # "root_block": False,
                        # "fastleave": False,
                        # "learning": True,
                        # "flood": True,
                        # "id": "0x8003",
                        # "no": "0x3",
                        "designated_port": int(member["port"]),
                        "designated_cost": int(member["cost"]),
                        "bridge_id": bridge["id"],
                        "root_id": bridge["root_id"],
                        # "hold_timer": 0.00,
                        # "message_age_timer": 0.00,
                        # "forward_delay_timer": 0.00,
                        # "topology_change_ack": 0,
                        # "config_pending": 0,
                        # "proxy_arp": False,
                        # "proxy_arp_wifi": False,
                        # "multicast_router": 1,
                        # "mcast_flood": True,
                        # "mcast_to_unicast": False,
                        # "neigh_suppress": False,
                        # "group_fwd_mask": "0",
                        # "group_fwd_mask_str": "0x0",
                        # "vlan_tunnel": False,
                        # "isolated": False,
                    }
        return None

    def _get_linkinfo(self):
        return {
            "info_kind": self._get_info_kind(),
            "info_data": self._get_info_data(),
            "info_slave_kind": self._get_info_slave_kind(),
            "info_slave_data": self._get_info_slave_data(),
        }

    def _get_addr_info(self):
        addr_info = []
        for inet in self._ifconfig.get("address", []):
            ip = Prefix(inet["address"])
            addr = {"family": inet["family"], "local": inet["address"]}
            if inet.get("peer"):
                addr["address"] = inet["peer"]
            if find_item(inet, "prefixlen"):
                addr["prefixlen"] = inet["prefixlen"]
            elif find_item(inet, "netmask"):
                addr["prefixlen"] = netmask_to_length(inet["netmask"])
            if find_item(inet, "broadcast"):
                addr["broadcast"] = inet["broadcast"]
            if ip.is_link:
                addr["scope"] = "link"
            elif ip.is_global:
                # NOTE: may be Python ipaddress is_global() is not compliant with iproute2
                addr["scope"] = "global"
            else:
                addr["scope"] = "host"
            if inet["family"] == "inet":
                addr["label"] = self._ifconfig["interface"]
            addr["valid_life_time"] = (
                inet["vltime"] if inet.get("vltime") is not None else _ND6_INFINITE_LIFETIME
            )
            addr["preferred_life_time"] = (
                inet["pltime"] if inet.get("pltime") is not None else _ND6_INFINITE_LIFETIME
            )
            # TODO:
            # "dynamic": true,
            # "mngtmpaddr": true
            # "noprefixroute": true
            addr_info.append(addr)
        return addr_info

    def str(self, details=True):
        data = self.dict(details=details)
        res = dict_format(data, "{}: {}", "ifindex", "ifname")
        res += dict_format(data, "@{}", "link")
        res += f": <{','.join(self['flags'])}> mtu {self['mtu']}"
        res += dict_format(data, " master {}", "master")
        res += dict_format(data, " state {}", "operstate")
        res += dict_format(data, " qlen {}", "txqlen")
        res += "\n"

        res += dict_format(data, "    link/{}", "link_type")
        res += dict_format(data, " {}", "address")
        res += dict_format(
            data, " peer {}" if self._data["link_pointtopoint"] else " brd {}", "broadcast"
        )
        res += dict_format(data, " minmtu {}", "min_mtu")
        res += dict_format(data, " maxmtu {}", "max_mtu")
        res += dict_format(data, " numtxqueues {}", "num_tx_queues")
        res += dict_format(data, " numrxqueues {}", "num_rx_queues")
        res += dict_format(data, " gso_max_size {}", "gso_max_size")
        res += dict_format(data, " gso_max_segs {}", "gso_max_segs")
        res += "\n"

        if data.get("linkinfo", {}).get("info_kind"):
            info = data["linkinfo"]
            res += dict_format(info, "    {}", "info_kind")
            if info["info_kind"] == "vlan":
                res += dict_format(info.get("info_data"), " protocol {} id {} ", "protocol", "id")
            elif info["info_kind"] == "bridge":
                res += "".join(
                    [f" {key} {value}" for key, value in info.get("info_data", {}).items()]
                )
            res += "\n"

        ips = []
        for addr in data.get("addr_info", []):
            if addr["family"] == "inet" and int(addr["prefixlen"]) < 32:
                local = Prefix(f'{addr["local"]}/{addr["prefixlen"]}')
                secondary = any(local in ip for ip in ips)
                ips.append(local)
            else:
                secondary = False
            res += dict_format(addr, "    {} {}", "family", "local")
            res += dict_format(addr, " peer {}", "address")
            res += dict_format(addr, "/{}", "prefixlen")
            res += dict_format(addr, " brd {}", "broadcast")
            res += dict_format(addr, " scope {}", "scope")
            if secondary:
                res += " secondary"
            res += dict_format(addr, " {}", "label")
            if "valid_life_time" in addr and "preferred_life_time" in addr:
                res += "\n" "       valid_lft " + (
                    "forever"
                    if addr["valid_life_time"] == _ND6_INFINITE_LIFETIME
                    else str(addr["valid_life_time"])
                ) + " preferred_lft " + (
                    "forever"
                    if addr["preferred_life_time"] == _ND6_INFINITE_LIFETIME
                    else str(addr["preferred_life_time"])
                )
            res += "\n"

        return res.rstrip()


class _Bridge(_IpAddress):
    _OPTIONAL_FIELDS = {
        "hairpin": None,
        "guard": None,
        "root_block": None,
        "fastleave": None,
        "learning": None,
        "flood": None,
        "mcast_flood": None,
        "mcast_to_unicast": None,
        "neigh_suppress": None,
        "vlan_tunnel": None,
        "isolated": None,
    }

    def __init__(self, text):
        self._ifconfig = _Ifconfig(text)
        self._name = self._ifconfig._name
        self._data = {
            "ifindex": self._ifconfig["index"],
            "link": self._get_link(),
            "ifname": self._name,
            "flags": self._ifconfig["flags"],
            "mtu": self._ifconfig["mtu"],
            "master": None,  # async __update__ with self._get_master()
        }

    def __update__(self):
        if self.link == self:
            self._data["master"] = self._name
        else:
            bridge = self.link._ifconfig._data["bridge"]
            member = next(
                member for member in bridge["member"] if member["interface"] == self._name
            )
            self._data.update(
                {
                    "master": self.link.name,
                    "state": "forwarding",  # FIXME: how to check the state?
                    "priority": int(member["priority"]),
                    "cost": int(member["cost"]),
                    # "hairpin": False,
                    # "guard": False,
                    # "root_block": False,
                    # "fastleave": False,
                    # "learning": True,
                    # "flood": True,
                    # "mcast_flood": True,
                    # "mcast_to_unicast": False,
                    # "neigh_suppress": False,
                    # "vlan_tunnel": False,
                    # "isolated": False,
                }
            )

    def str(self, details=True):
        data = self.dict(details=details)
        res = dict_format(data, "{}: {}", "ifindex", "ifname")
        res += dict_format(data, "@{}", "link")
        res += f": <{','.join(self['flags'])}> mtu {self['mtu']}"
        res += dict_format(data, " master {}", "master")
        res += dict_format(data, " state {}", "state")
        res += dict_format(data, " priority {}", "priority")
        res += dict_format(data, " cost {}", "cost")
        return res


class Ifconfig(_Items):
    _kind = _Ifconfig

    def __init__(self):
        res = utils.shell(_IFCONFIG, *_IFCONFIG_OPTS)
        for text in re.findall(r"(^\w+:.*$\n(?:^\t.*$\n*)*)", res, flags=re.MULTILINE):
            # for every single interface:
            self.append(self._kind(text=text))

    def exist(self, interface):
        return any(item.name == interface for item in self._data)


class IpAddress(Ifconfig):
    _kind = _IpAddress

    def __init__(self):
        super().__init__()
        self._link_interfaces()

    def _link_interfaces(self):
        """
        Look up for bond/bridge interface relations
        """
        for item in self._data:
            for index, member in enumerate(item._ifconfig.get("bond", [])):
                if member is None:
                    continue
                self.lookup("ifname", member).link = item
            if item._ifconfig.get("bridge"):
                for member in item._ifconfig["bridge"].get("member", []):
                    self.lookup("ifname", member["interface"]).link = item
        for item in self._data:
            item.__update__()


class Bridge(Ifconfig):
    _kind = _Bridge

    def __init__(self):
        super().__init__()
        self._link_interfaces()

    def _link_interfaces(self):
        """
        Look up for bridge interface relations
        """
        for item in self._data:
            if item._ifconfig.get("bridge"):
                item.link = item
                for member in item._ifconfig["bridge"].get("member", []):
                    self.lookup("ifname", member["interface"]).link = item
        self._data = [item for item in self._data if item.link]
        for item in self._data:
            item.__update__()


class _BridgeForward(_Item):
    __slots__ = ("_bridge", "_expire")
    _entry = re.compile(
        rf"(?P<lladdr>{LLADDR}) Vlan(?P<vlan>\d+) (?P<dev>\w+) (?P<expire>\d+) flags=(?P<flag>\w+)<(?P<flags>.*)>"
    )
    _OPTIONAL_FIELDS = {"expire": None}

    def __init__(self, bridge, text):
        res = _reDict(self._entry, text).data
        self._bridge = bridge
        self._expire = int(res["expire"])
        self._data = {
            "mac": res["lladdr"],
            "ifname": res["dev"],
            "vlan": int(res["vlan"]),
            "flags": res["flags"],
            "master": None,
            "state": "permanent" if self._expire == 0 else "",
        }

    @property
    def bridge(self):
        return self._bridge

    def str(self, details=True):
        data = self.dict(details=details)
        res = data["mac"]
        res += dict_format(data, " dev {}", "ifname")
        res += dict_format(data, " vlan {}", "vlan")
        res += dict_format(data, " {}", "state")
        return res


class FDB(_Items):
    def __init__(self):
        res = utils.shell(_IFCONFIG, "-l").split()
        for interface in res:
            if interface.startswith("bridge"):
                text = utils.shell(_IFCONFIG, interface, "addr")
                for entry in text.splitlines():
                    self.append(_BridgeForward(interface, entry))
