import re

import iproute4mac.libc as libc
import iproute4mac.utils as utils

from iproute4mac.prefix import Prefix


_IFCONFIG = "ifconfig"
_IFCONFIG_OPTS = ["-f", "inet:cidr,inet6:cidr", "-L", "-m", "-v"]

_SYSCTL_RXQLEN = "net.link.generic.system.rcvq_maxlen"
_SYSCTL_TXQLEN = "net.link.generic.system.sndq_maxlen"
_TXQLEN = libc.sysctl(_SYSCTL_TXQLEN)

# nu <netinet6/nd6.h>
_ND6_INFINITE_LIFETIME = 0xFFFFFFFF

# map operstates
OPER_STATES = {"active": "UP", "inactive": "DOWN", "none": "UNKNOWN"}

_OPTIONAL_FIELDS = [
    "eflags",
    "xflags",
    "options",
    "capabilities",
    "hwassist",
    "promiscuity",
    "min_mtu",
    "max_mtu",
    "linkinfo",
    "num_tx_queues",
    "num_rx_queues",
    "gso_max_size",
    "gso_max_segs",
]

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
    __slots__ = "_data"

    def __init__(self, pattern, text):
        if not isinstance(pattern, re.Pattern):
            raise ValueError("pattern is not of {re.Pattern}")
        if not isinstance(text, str):
            raise ValueError("data is not of {str}")

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
                self._data.append(res.groupdict())
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
        return self.groupdict()

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
        r"\t\s+hostfilter (?P<hostfilter>\d+) hw: (?P<hw>\S+) ip: (?P<ip>\S+)"
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


class _IfconfigBase:
    _name = None
    _data = None
    _link = None

    def __init__(self):
        raise NotImplementedError

    def __contains__(self, element):
        return not utils.empty(self._data.get(element))

    def __iter__(self):
        for key, value in self._data:
            yield key, value

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        if key in self._data:
            del self._data[key]

    def __str__(self):
        return self.str()

    def get(self, key, default=None):
        return self._data.get(key, default)

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

    def data(self, details=True):
        res = {}
        for key, value in self._data.items():
            if value is None:
                continue
            if key not in _OPTIONAL_FIELDS or details:
                res[key] = value
        return res

    def present(self, key, value=None, recurse=False, strict=False):
        return utils.find_item(self._data, key, value=value, recurse=recurse, strict=strict)

    def _value(self, key, value):
        return value

    def _dict(self, data):
        res = {}
        for key, value in data.items():
            value = self._value(key, value)
            if not utils.empty(value):
                res[key] = value
        return res

    def dict(self, details=True):
        return self._dict(self.data(details=details))

    def str(self, details=True):
        raise NotImplementedError


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
    _address = re.compile(
        r"\t(?P<family>inet|inet6) (?P<address>[^/^%]+)(?:%(?P<net>\w+))?"
        r"(?: --> (?P<peer>[^/^%]+)(?:%\S+)?)?"
        r"(?:/(?P<prefixlen>\d+))?"
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
    _effective_interface = re.compile(r"\teffective interface: (?P<interface>\w+)")
    _link_rate = re.compile(r"\tlink rate: (?P<rate>[\d\.]+) (?P<rate_um>\w+)")
    _uplink_rate = re.compile(
        r"\tuplink rate: (?P<eff>[\d\.]+) (?P<eff_um>\w+) \[eff\] / (?P<max>[\d\.]+) (?P<max_um>\w+)"
    )
    _downlink_rate = re.compile(
        r"\tdownlink rate: (?P<eff>[\d\.]+) (?P<eff_um>\w+) \[eff\] / (?P<max>[\d\.]+) (?P<max_um>\w+)"
    )
    _timestamp = re.compile(r"\ttimestamp: (?P<timestamp>\w+)")
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
            "link_type": "none",
            "agent": _reList(self._agent, text).data,
            "link_quality": _reDict(self._link_quality, text).data,
            "state_availability": _reDict(self._state_availability, text).data,
            "scheduler": _reDict(self._scheduler, text).data,
            "effective_interface": _reDict(self._effective_interface, text).data,
            "link_rate": _reDict(self._link_rate, text).data,
            "uplink_rate": _reDict(self._uplink_rate, text).data,
            "downlink_rate": _reDict(self._downlink_rate, text).data,
            **_reDict(self._timestamp, text).data,
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

    def __iter__(self):
        for key, value in self._data:
            yield key, self._value(key, value)

    def __getitem__(self, key):
        return self._value(key, self._data[key])

    def get(self, key, default=None):
        return self._value(key, self._data.get(key, default))

    def _cast(self, value):
        if value.isdigit():
            return int(value)
        if value.replace(".", "", 1).isdigit():
            return float(value)
        if value == "<none>":
            return None
        if utils.strcmp(value, "true", "yes", "enabled", case=False):
            return True
        if utils.strcmp(value, "false", "no", "disabled", case=False):
            return False
        return value

    def _value(self, key, value):
        if isinstance(value, dict):
            return self._dict(value)
        if isinstance(value, list):
            return self._list(value)
        if key == "flag":
            return value
        if key == "flags":
            return value.split(",") if value else []
        if key == "list":
            return value.split(" ") if value else []
        if value is not None:
            return self._cast(value)
        return value

    def _list(self, data):
        res = []
        for value in data:
            if isinstance(value, dict):
                value = self._dict(value)
            elif isinstance(value, list):
                value = self._list(value)
            elif value is not None:
                value = self._cast(value)
            res.append(value)
        return res

    def str(self, details=True):
        data = self.data(details=details)
        res = f"{self._name}: flags={data['flag']}<{data['flags']}>"
        res += utils.dict_format(data, " mtu {}", "mtu")
        res += utils.dict_format(data, " rtref {}", "rtref")
        res += f" index {data['index']}\n"
        for flags in ["eflags", "xflags", "options", "capabilities", "hwassist"]:
            if data.get(flags):
                res += f"\t{flags}={data[flags]['flag']}<{data[flags]['flags']}>\n"
        if self._data["link_type"] != "loopback":
            res += utils.dict_format(data, "\tether {}\n", "ether")
        if data.get("bridge"):
            bridge = data["bridge"]
            res += "\tConfiguration:\n"
            res += f"\t\tid {bridge['id']} priority {bridge['priority']} hellotime {bridge['hellotime']} fwddelay {bridge['fwddelay']}\n"
            res += f"\t\tmaxage {bridge['maxage']} holdcnt {bridge['holdcnt']} proto {bridge['proto']} maxaddr {bridge['maxaddr']} timeout {bridge['timeout']}\n"
            res += f"\t\troot id {bridge['root_id']} priority {bridge['root_priority']} ifcost {bridge['root_cost']} port {bridge['root_port']}\n"
            res += f"\t\tipfilter {bridge['ipfilter']} flags {bridge['flag']}\n"
            for member in bridge.get("member", []):
                res += (
                    f"\tmember: {member['interface']} flags={member['flag']}<{member['flags']}>\n"
                )
                res += f"\t        ifmaxaddr {member['ifmaxaddr']} port {member['port']} priority {member['priority']} path cost {member['cost']}\n"
                res += f"\t        hostfilter {member['hostfilter']} hw: {member['hw']} ip: {member['ip']}\n"
            # res += "\tAddress cache:\n"
        if self.name.startswith("feth"):
            res += utils.dict_format(data, "\tpeer: {}\n", "peer", default="<none>")
        for addr in data.get("address", []):
            res += f"\t{addr['family']} {addr['address']}"
            res += utils.dict_format(addr, "%{}", "net")
            res += utils.dict_format(addr, " --> {}", "peer")
            res += utils.dict_format(addr, "/{}", "prefixlen")
            res += utils.dict_format(addr, " broadcast {}", "broadcast")
            res += utils.dict_format(addr, " {}", "autoconf")
            res += utils.dict_format(addr, " {}", "secured")
            res += utils.dict_format(addr, " pltime {}", "pltime")
            res += utils.dict_format(addr, " vltime {}", "vltime")
            res += utils.dict_format(addr, " scopeid {}", "scopeid")
            res += "\n" if addr["family"] == "inet" else " \n"
        res += utils.dict_format(
            data.get("vlan"), "\tvlan: {} parent interface: {}\n", "vlanid", "parent"
        )
        res += utils.dict_format(data, "\tnetif: {}\n", "netif")
        res += utils.dict_format(data, "\tflowswitch: {}\n", "flowswitch")
        if data.get("nd6_options"):
            res += f"\tnd6 options={data['nd6_options']['flag']}<{data['nd6_options']['flags']}>\n"
        res += utils.dict_format(data, "\tmedia: {}\n", "media")
        res += utils.dict_format(data, "\tstatus: {}\n", "status")
        if data.get("media"):
            res += "\tsupported media:\n"
            for media in data.get("supported_media", []):
                if media["type"]:
                    res += utils.dict_format(media, "\t\tmedia {}", "type")
                    for opt in media["opts"]:
                        res += f" mediaopt {opt}"
                else:
                    res += "\t\t<unknown type>"
                res += "\n"
        if self._name.startswith("bond"):
            members = " ".join(data["bond"]) if data["bond"] else "<none>"
            res += f"\tbond interfaces: {members}\n"
        res += utils.dict_format(data, "\tgeneration id: {}\n", "generation_id")
        res += utils.dict_format(data, "\ttype: {}\n", "type")
        for agent in data.get("agent", []):
            res += utils.dict_format(
                agent,
                '\tagent domain:{} type:{} flags:{} desc:"{}"\n',
                "domain",
                "type",
                "flag",
                "desc",
            )
        res += utils.dict_format(
            data.get("link_quality"), "\tlink quality: {} ({})\n", "quality", "desc"
        )
        res += utils.dict_format(
            data.get("state_availability"),
            "\tstate availability: {} ({})\n",
            "availability",
            "desc",
        )
        res += utils.dict_format(data.get("scheduler"), "\tscheduler: {} {}\n", "type", "desc")
        res += utils.dict_format(data, "\teffective interface: {}\n", "effective_interface")
        res += utils.dict_format(data.get("link_rate"), "\tlink rate: {} {}\n", "rate", "rate_um")
        res += utils.dict_format(
            data.get("uplink_rate"),
            "\tuplink rate: {} {} [eff] / {} {}\n",
            "eff",
            "eff_um",
            "max",
            "max_um",
        )
        res += utils.dict_format(
            data.get("downlink_rate"),
            "\tdownlink rate: {} {} [eff] / {} {} [max]\n",
            "eff",
            "eff_um",
            "max",
            "max_um",
        )
        res += utils.dict_format(data, "\ttimestamp: {}\n", "timestamp")
        res += utils.dict_format(
            data.get("qosmarking"),
            "\tqosmarking enabled: {} mode: {}\n",
            "enabled",
            "mode",
        )
        res += utils.dict_format(data, "\tlow power mode: {}\n", "low_power_mode")
        res += utils.dict_format(data, "\tmulti layer packet logging (mpklog): {}\n", "mpklog")
        res += utils.dict_format(data, "\troutermode4: {}\n", "routermode4")
        res += utils.dict_format(data, "\troutermode6: {}\n", "routermode6")
        return res.rstrip()


class _IpAddress(_IfconfigBase):
    __slots__ = ("_ifconfig",)

    def __init__(self, text):
        self._ifconfig = _Ifconfig(text)
        self._name = self._ifconfig._name
        self._data = {
            "ifindex": self._ifconfig["index"],
            "link": None,  # async __update__ with self._get_link()
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
            "link_type": self._ifconfig.get("link_type", "none"),
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

    def __update__(self):
        self._data.update(
            {
                "link": self._get_link(),
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
        if self.link:
            return self.link.name
        return None

    def _get_info_kind(self):
        if utils.startwith(self._ifconfig["interface"], "bridge", "bond", "feth", "vlan"):
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
                }
            )
        return info_data if info_data else None

    def _get_info_slave_kind(self):
        if self.link:
            return self.link._get_info_kind()
        return None

    def _get_info_slave_data(self):
        if self._ifconfig.link:
            if self._ifconfig.link.name.startswith("bond"):
                # FIXME: where to find original hardawre lladdr?
                return {"perm_hwaddr": self._ifconfig["ether"]}
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
            if utils.find_item(inet, "prefixlen"):
                addr["prefixlen"] = inet["prefixlen"]
            if utils.find_item(inet, "netmask"):
                addr["prefixlen"] = netmask_to_length(inet["netmask"])
            if utils.find_item(inet, "broadcast"):
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

    def _value(self, key, value):
        if isinstance(value, dict):
            return self._dict(value)
        if isinstance(value, list):
            return self._list(value)
        return value

    def _list(self, data):
        res = []
        for value in data:
            if isinstance(value, dict):
                value = self._dict(value)
            elif isinstance(value, list):
                value = self._list(value)
            res.append(value)
        return res

    def str(self, details=None):
        data = self.data(details=details)
        res = utils.dict_format(data, "{}: {}", "ifindex", "ifname")
        res += utils.dict_format(data, "@{}", "link")
        res += f": <{','.join(self['flags'])}> mtu {self['mtu']}"
        res += utils.dict_format(data, " master {}", "master")
        res += utils.dict_format(data, " state {}", "operstate")
        res += utils.dict_format(data, " qlen {}", "txqlen")
        res += "\n"

        res += utils.dict_format(data, "    link/{}", "link_type")
        res += utils.dict_format(data, " {}", "address")
        res += utils.dict_format(data, " brd {}", "broadcast")
        res += utils.dict_format(data, " minmtu {}", "min_mtu")
        res += utils.dict_format(data, " maxmtu {}", "max_mtu")
        res += utils.dict_format(data, " numtxqueues {}", "num_tx_queues")
        res += utils.dict_format(data, " numrxqueues {}", "num_rx_queues")
        res += utils.dict_format(data, " gso_max_size {}", "gso_max_size")
        res += utils.dict_format(data, " gso_max_segs {}", "gso_max_segs")
        res += "\n"

        if data.get("linkinfo", {}).get("info_kind"):
            info = data["linkinfo"]
            res += utils.dict_format(info, "    {}", "info_kind")
            if info["info_kind"] == "vlan":
                res += utils.dict_format(
                    info.get("info_data"), " protocol {} id {} ", "protocol", "id"
                )
            elif info["info_kind"] == "bridge":
                res += "".join(
                    [f" {key} {value}" for key, value in info.get("info_data", {}).items()]
                )
            res += "\n"

        ips = []
        for addr in data.get("addr_info", []):
            if addr["family"] == "inet" and addr["prefixlen"] < 32:
                local = Prefix(f'{addr["local"]}/{addr["prefixlen"]}')
                secondary = any(local in ip for ip in ips)
                ips.append(local)
            else:
                secondary = False
            res += utils.dict_format(addr, "    {} {}", "family", "local")
            res += utils.dict_format(addr, " peer {}", "peer")
            res += utils.dict_format(addr, "/{}", "prefixlen")
            res += utils.dict_format(addr, " brd {}", "broadcast")
            res += utils.dict_format(addr, " scope {}", "scope")
            if secondary:
                res += " secondary"
            res += utils.dict_format(addr, " {}", "label")
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


class Ifconfig:
    __slots__ = "_interfaces"
    _kind = _Ifconfig

    def __init__(self):
        self._interfaces = []
        res = utils.shell(_IFCONFIG, *_IFCONFIG_OPTS, "-a")
        for text in re.findall(r"(^\w+:.*$\n(?:^\t.*$\n*)*)", res, flags=re.MULTILINE):
            # for every single interface:
            self._interfaces.append(self._kind(text=text))

    def __iter__(self):
        for interface in self._interfaces:
            yield interface

    def __str__(self):
        return "\n".join(map(str, self._interfaces))

    def __len__(self):
        return len(self._interfaces)

    def __getitem__(self, index):
        return self._interfaces[index]

    def pop(self, index=-1):
        return self._interfaces.pop(index)

    def set(self, interfaces):
        if not isinstance(interfaces, list) or not all(
            isinstance(i, _IfconfigBase) for i in interfaces
        ):
            raise ValueError(f"argument is not list() of '{_IfconfigBase}'>")
        self._interfaces = interfaces

    def exist(self, interface):
        return any(i.name == interface for i in self._interfaces)

    def lookup(self, key, value):
        """
        Lookup for element in list with list[ley] == value
        """
        return next((i for i in self._interfaces if i.present(key, value)), None)

    def dict(self, details=None):
        return [interface.dict(details=details) for interface in self._interfaces]

    # alias self.list() as self.dict()
    list = dict

    def str(self, details=None):
        return "\n".join([interface.str(details=details) for interface in self._interfaces])

    @property
    def interfaces(self):
        return self._interfaces


class IpAddress(Ifconfig):
    _kind = _IpAddress

    def __init__(self):
        super().__init__()
        self._link_interfaces()

    def _link_interfaces(self):
        """
        Look up for bond/bridge interface relations
        """
        for interface in self._interfaces:
            for index, member in enumerate(interface._ifconfig.get("bond", [])):
                if member is None:
                    continue
                if isinstance(member, str):
                    self.lookup("ifname", member).link = interface
            if interface._ifconfig.get("bridge"):
                for member in interface._ifconfig["bridge"].get("member", []):
                    if isinstance(member["interface"], str):
                        self.lookup("ifname", member["interface"]).link = interface
        for interface in self._interfaces:
            interface.__update__()
