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
    return utils.shell(_IFCONFIG, *argv, fatal=fatal)


def netmask_to_length(mask):
    return utils.bit_count(int(mask, 16))


def dict_filter(data, details=True):
    """
    Recursively remove empty values
    """

    res = {}
    for key, value in list(data.items()):
        if details or key not in _OPTIONAL_FIELDS:
            if isinstance(value, dict):
                res[key] = dict_filter(value, details=details)
            elif value is not None:
                res[key] = value
    return res


class _IfconfigBase:
    """
    Basic interface dictionary representation of macOS ifconfig output
    """

    __slots__ = ("_properties", "_header", "_ifconfig", "_data", "_dump")

    def __init__(self, properties, header):
        if not isinstance(properties, dict):
            raise ValueError(f"properties ({type(properties)}) is not <class 'dict'>")
        if header not in properties:
            raise ValueError(f"field '{header}' not present in properties dict")
        self._properties = properties
        self._header = header
        self._data = {}
        self._ifconfig = {}
        for key in self._properties:
            if self._properties[key]:
                self._ifconfig.update(self._decode(key))
        self._dump = self._ifconfig

    def __update__(self):
        self._data.update(self._dict)

    def __contains__(self, other):
        return other in self._dump

    def __str__(self):
        return self.str()

    def __iter__(self):
        for k, v in self._dump:
            yield k, v

    def __getitem__(self, key):
        return self._dump.get(key)

    def __setitem__(self, key, value):
        self._dump[key] = value

    def __delitem__(self, key):
        if key in self._dump:
            del self._dump[key]

    def _format(self, string, *fields, default=None):
        return utils.dict_format(self._dump, string, *fields, default=default)

    def present(self, key, value=None, recurse=False, strict=False):
        return utils.find_item(self._dump, key, value=value, recurse=recurse, strict=strict)

    def visible(self, key, recurse=False, details=None):
        if details is None:
            details = self._details
        return utils.find_item(self._dump, key, recurse=recurse) and (
            details or key not in _OPTIONAL_FIELDS
        )

    def get(self, key, value=None):
        return self._dump.get(key, value) if self.visible(key) else value

    def pop(self, key, value=None):
        if value is None:
            return self._dump.pop(key)
        return self._dump.pop(key, value)

    @property
    def name(self):
        return self._ifconfig.get(self._header)

    @property
    def index(self):
        return self._ifconfig.get("index")

    @staticmethod
    def _groupdict(entry):
        """
        Type conversion of groupdict() entries (strings, flags, lists, and numbers)
        """
        res = entry.groupdict()
        for key, value in res.items():
            if key == "flags":
                res[key] = value.split(",") if value else []
            elif key == "list":
                res[key] = value.split(" ") if value else []
            elif value is None:
                # keep check of empty after flags/list to allow empty list
                continue
            elif value.isdigit():
                res[key] = int(value)
            elif value.replace(".", "", 1).isdigit():
                res[key] = float(value)
            elif value == "<none>":
                res[key] = None
        return res

    def _decode(self, entry):
        """
        Expand groupdict()
        """
        if self._properties.get(entry) is None:
            res = None
        elif isinstance(self._properties[entry], _IfconfigBase):
            # copy (link) complex data (e.g. bridge info)
            res = self._properties[entry]._ifconfig
        elif hasattr(self._properties[entry], "__iter__"):
            # re.search() multiple entries
            res = [self._groupdict(e) for e in self._properties[entry]]
        elif len(res := self._groupdict(self._properties[entry])) == 1:
            # treat sinfle field dict as a simple value (e.g. {"a":1} -> 1)
            res = res[next(iter(res))]
        elif "hex" in res and "flags" in res:
            # flags special case
            res = {f"x_{entry}": res["hex"], entry: res["flags"]}
            entry = self._header
        return {entry: res} if entry != self._header else res

    @property
    def _dict(self):
        # dict() will ensure to copy avoiding linking
        return dict(self._dump)

    def dict(self):
        raise NotImplementedError

    def str(self):
        raise NotImplementedError


class _Bridge(_IfconfigBase):
    """
    Specific bridge dictionary representation of macOS ifconfig output
    """

    _bridge = re.compile(
        r"\tConfiguration:\n"
        rf"\t\s+id (?P<id>{LLADDR}) priority (?P<priority>\d+) hellotime (?P<hellotime>\d+) fwddelay (?P<fwddelay>\d+)\n"
        r"\t\s+maxage (?P<maxage>\d+) holdcnt (?P<holdcnt>\d+) proto (?P<proto>\w+) maxaddr (?P<maxaddr>\d+) timeout (?P<timeout>\d+)\n"
        rf"\t\s+root id (?P<root_id>{LLADDR}) priority (?P<root_priority>\d+) ifcost (?P<root_cost>\d+) port (?P<root_port>\d+)\n"
        r"\t\s+ipfilter (?P<ipfilter>\w+) flags (?P<flag>0x[0-9a-fA-F]+)"
    )
    _member = re.compile(
        rf"\tmember: (?P<interface>{IFNAME}) flags=(?P<x_flags>\w+)<(?P<flags>.*)>\n"
        r"\t\s+ifmaxaddr (?P<ifmaxaddr>\d+) port (?P<port>\d+) priority (?P<priority>\d+) path cost (?P<cost>\d+)\n"
        rf"\t\s+hostfilter (?P<hostfilter>\d+) hw: (?P<hw>{LLADDR}) ip: (?P<ip>{IPV4ADDR}|{IPV6ADDR})"
    )
    # TODO: how to catch address cache?
    # _address_cache = re.compile(...)

    def __init__(self, data):
        properties = {"bridge": self._bridge.search(data), "member": self._member.finditer(data)}
        super().__init__(properties, "bridge")


class _Ifconfig(_IfconfigBase):
    """
    Specific interface dictionary representation of macOS ifconfig output
    """

    __slots__ = ("_details",)
    _interface = re.compile(
        r"(?P<interface>\w+): flags=(?P<x_flags>\w+)<(?P<flags>.*)>"
        r" mtu (?P<mtu>\d+)?"
        r"(?: rtref (?P<rtref>\d+))?"
        r" index (?P<index>\d+)"
    )
    _eflags = re.compile(r"\teflags=(?P<hex>\w+)<(?P<flags>.*)>")
    _xflags = re.compile(r"\txflags=(?P<hex>\w+)<(?P<flags>.*)>")
    _options = re.compile(r"\toptions=(?P<hex>\w+)<(?P<flags>.*)>")
    _capabilities = re.compile(r"\tcapabilities=(?P<hex>\w+)<(?P<flags>.*)>")
    _hwassist = re.compile(r"\thwassist=(?P<hex>\w+)<(?P<flags>.*)>")
    _ether = re.compile(rf"\tether (?P<ether>{LLADDR})")
    _bridge = re.compile(r"\tConfiguration:\n(?:\t\t.*\n)+(?:\tmember: .*\n(?:\t\s+.*\n)+)*")
    _peer = re.compile(r"\s+peer: (?P<peer>\w+)")
    _inet = re.compile(
        rf"\tinet (?P<address>{IPV4ADDR})"
        rf"(?: --> (?P<peer>{IPV4ADDR}))?"
        r"(?:/(?P<prefixlen>\d+))?"
        rf"(?: broadcast (?P<broadcast>{IPV4ADDR}))?"
    )
    _inet6 = re.compile(
        rf"\tinet6 (?P<address>{IPV6ADDR})(?:%(?P<net>\w+))?"
        rf"(?: --> (?P<peer>{IPV6ADDR})(?:%\w+)?)?"
        r"(?:/(?P<prefixlen>\d+))?"
        r"(?: (?P<autoconf>autoconf))?"
        r"(?: (?P<secured>secured))?"
        r"(?: pltime (?P<pltime>\d+))?"
        r"(?: vltime (?P<vltime>\d+))?"
        r"(?: scopeid (?P<scopeid>0x[0-9a-fA-F]+))?"
    )
    _vlan = re.compile(rf"\s+vlan: (?P<vlanid>\d+) parent interface: (?P<parent>\<none\>|{IFNAME})")
    _netif = re.compile(rf"\tnetif: (?P<netif>{NETIF})")
    _flowswitch = re.compile(rf"\tflowswitch: (?P<flowswitch>{NETIF})")
    _nd6_options = re.compile(r"\tnd6 options=(?P<hex>\w+)<(?P<flags>.*)>")
    _media = re.compile(r"\tmedia: (?P<media>.+)")
    _status = re.compile(r"\tstatus: (?P<status>\w+)")
    # _supported_media = re.compile(r"\tsupported media:\n(?:\t\t.*\n)+")
    _supported_media = re.compile(
        r"\t\t(?:media (?P<media>[\w-]+)(?: mediaopt (?P<mediaopt>[\w-]+))?|<unknown type>)"
    )
    _bond = re.compile(rf"\s+bond interfaces: (?P<list>{IFNAME}(?: {IFNAME}+)*)")
    _generation_id = re.compile(r"\tgeneration id: (?P<generation_id>\d+)")
    _type = re.compile(r"\ttype: (?P<type>.*)$", flags=re.MULTILINE)
    _agent = re.compile(
        r'\tagent domain:(?P<domain>[\w\.]+) type:(?P<type>\w+) flags:(?P<flag>0x[0-9a-fA-F]+) desc:"(?P<desc>.*)"'
    )
    _link_quality = re.compile(r"\tlink quality: (?P<value>\d+) \((?P<desc>\w+)\)")
    _state_availability = re.compile(r"\tstate availability: (?P<value>\d+) \((?P<desc>\w+)\)")
    _scheduler = re.compile(r"\tscheduler: (?P<value>\w+)(?: (?P<desc>.*))?")
    _effective_interface = re.compile(rf"\teffective interface: (?P<interface>{IFNAME})")
    _link_rate = re.compile(r"\tlink rate: (?P<rate>[\d\.]+) (?P<rate_um>\w+)")
    _uplink_rate = re.compile(
        r"\tuplink rate: (?P<eff>[\d\.]+) (?P<eff_um>\w+) \[eff\] / (?P<max>[\d\.]+) (?P<max_um>\w+)"
    )
    _downlink_rate = re.compile(
        r"\tdownlink rate: (?P<eff>[\d\.]+) (?P<eff_um>\w+) \[eff\] / (?P<max>[\d\.]+) (?P<max_um>\w+)"
    )
    _timestamp = re.compile(r"\ttimestamp: (?P<mode>\w+)")
    _qosmarking = re.compile(r"\tqosmarking enabled: (?P<enabled>\w+) mode: (?P<mode>\w+)")
    _low_power_mode = re.compile(r"\tlow power mode: (?P<mode>\w+)")
    _mpklog = re.compile(r"\tmulti layer packet logging \(mpklog\): (?P<mode>\w+)")
    _routermode4 = re.compile(r"\troutermode4: (?P<mode>\w+)")
    _routermode6 = re.compile(r"\troutermode6: (?P<mode>\w+)")

    def __init__(self, interface=None, data=None, details=True):
        if interface is None and data is None:
            raise ValueError("no input data (interface or data required)")
        if interface is not None and data is not None:
            raise ValueError("multiple input data (interface or data required)")
        if interface:
            data = utils.shell(_IFCONFIG, *_IFCONFIG_OPTS, interface)
        properties = {
            "interface": self._interface.search(data),
            "eflags": self._eflags.search(data),
            "xflags": self._xflags.search(data),
            "options": self._options.search(data),
            "capabilities": self._capabilities.search(data),
            "hwassist": self._hwassist.search(data),
            "ether": self._ether.search(data),
            "bridge": self._search_bridge(data),
            "peer": self._peer.search(data),
            "inet": self._inet.finditer(data),
            "inet6": self._inet6.finditer(data),
            "vlan": self._vlan.search(data),
            "netif": self._netif.search(data),
            "flowswitch": self._flowswitch.search(data),
            "nd6_options": self._nd6_options.search(data),
            "media": self._media.search(data),
            "status": self._status.search(data),
            "supported_media": self._supported_media.finditer(data),
            "bond": self._bond.search(data),
            "generation_id": self._generation_id.search(data),
            "type": self._type.search(data),
            "agent": self._agent.finditer(data),
            "link_quality": self._link_quality.search(data),
            "state_availability": self._state_availability.search(data),
            "scheduler": self._scheduler.search(data),
            "effective_interface": self._effective_interface.search(data),
            "link_rate": self._link_rate.search(data),
            "uplink_rate": self._uplink_rate.search(data),
            "downlink_rate": self._downlink_rate.search(data),
            "timestamp": self._timestamp.search(data),
            "qosmarking": self._qosmarking.search(data),
            "low_power_mode": self._low_power_mode.search(data),
            "mpklog": self._mpklog.search(data),
            "routermode4": self._routermode4.search(data),
            "routermode6": self._routermode6.search(data),
        }
        super().__init__(properties, "interface")
        if "LOOPBACK" in self._ifconfig["flags"]:
            self._ifconfig["link_type"] = "loopback"
            self._ifconfig["lladdress"] = "00:00:00:00:00:00"
            self._ifconfig["llbroadcast"] = "00:00:00:00:00:00"
        if self._ifconfig.get("ether"):
            self._ifconfig["lladdress"] = self._ifconfig["ether"]
            self._ifconfig["llbroadcast"] = "ff:ff:ff:ff:ff:ff"
            self._ifconfig["link_type"] = "ether"
        self._details = details

    @property
    def details(self):
        return self._details

    @details.setter
    def details(self, value):
        self._details = value

    @property
    def name(self):
        return self._ifconfig.get("interface")

    @property
    def index(self):
        return self._ifconfig.get("index")

    def _search_bridge(self, data):
        """
        Adding bridge data
        """
        if res := self._bridge.search(data):
            return _Bridge(res.group())
        return None

    def dict(self, details=None):
        return dict_filter(self._dump, details if details is not None else self._details)

    def str(self, details=None):
        res = f"{self._ifconfig['interface']}: flags={self._ifconfig['x_flags']}<{','.join(self._ifconfig['flags'])}>"
        res += self._format(" mtu {}", "mtu")
        res += self._format(" rtref {}", "rtref")
        res += f" index {self._ifconfig['index']}\n"
        for flags in ["eflags", "xflags", "options", "capabilities", "hwassist"]:
            if self._ifconfig.get(flags):
                res += (
                    f"\t{flags}={self._ifconfig['x_'+flags]}<{','.join(self._ifconfig[flags])}>\n"
                )
        res += self._format("\tether {}\n", "ether")
        if self._ifconfig.get("bridge"):
            bridge = self._ifconfig["bridge"]
            res += "\tConfiguration:\n"
            res += f"\t\tid {bridge['id']} priority {bridge['priority']} hellotime {bridge['hellotime']} fwddelay {bridge['fwddelay']}\n"
            res += f"\t\tmaxage {bridge['maxage']} holdcnt {bridge['holdcnt']} proto {bridge['proto']} maxaddr {bridge['maxaddr']} timeout {bridge['timeout']}\n"
            res += f"\t\troot id {bridge['root_id']} priority {bridge['root_priority']} ifcost {bridge['root_cost']} port {bridge['root_port']}\n"
            res += f"\t\tipfilter {bridge['ipfilter']} flags {bridge['flag']}\n"
            for member in bridge.get("member", []):
                res += f"\tmember: {member['interface']} flags={member['x_flags']}<{','.join(member['flags'])}>\n"
                res += f"\t        ifmaxaddr {member['ifmaxaddr']} port {member['port']} priority {member['priority']} path cost {member['cost']}\n"
                res += f"\t        hostfilter {member['hostfilter']} hw: {member['hw']} ip: {member['ip']}\n"
            # res += "\tAddress cache:\n"
        if self.name.startswith("feth"):
            res += self._format("\tpeer: {}\n", "peer", default="<none>")
        for family in ["inet", "inet6"]:
            for inet in self._ifconfig.get(family, []):
                res += f"\t{family} {inet['address']}"
                res += utils.dict_format(inet, "%{}", "net")
                res += utils.dict_format(inet, " --> {}", "peer")
                res += utils.dict_format(inet, "/{}", "prefixlen")
                res += utils.dict_format(inet, " broadcast {}", "broadcast")
                res += utils.dict_format(inet, " {}", "autoconf")
                res += utils.dict_format(inet, " {}", "secured")
                res += utils.dict_format(inet, " pltime {}", "pltime")
                res += utils.dict_format(inet, " vltime {}", "vltime")
                res += utils.dict_format(inet, " scopeid {}", "scopeid")
                res += "\n" if family == "inet" else " \n"
        res += utils.dict_format(
            self._ifconfig.get("vlan"), "\tvlan: {} parent interface: {}\n", "vlanid", "parent"
        )
        res += self._format("\tnetif: {}\n", "netif")
        res += self._format("\tflowswitch: {}\n", "flowswitch")
        if self._ifconfig.get("nd6_options"):
            res += f"\tnd6 options={self._ifconfig['x_nd6_options']}<{','.join(self._ifconfig['nd6_options'])}>\n"
        res += self._format("\tmedia: {}\n", "media")
        res += self._format("\tstatus: {}\n", "status")
        if self._ifconfig.get("media"):
            res += "\tsupported media:\n"
            for media in self._ifconfig.get("supported_media", []):
                if media["media"] is None and media["mediaopt"] is None:
                    res += "\t\t<unknown type>"
                else:
                    res += utils.dict_format(media, "\t\tmedia {}", "media")
                    res += utils.dict_format(media, " mediaopt {}", "mediaopt")
                res += "\n"
        if self._ifconfig["interface"].startswith("bond"):
            res += f"\tbond interfaces: {' '.join(self._ifconfig.get('bond', ['<none>']))}\n"
        res += self._format("\tgeneration id: {}\n", "generation_id")
        res += self._format("\ttype: {}\n", "type")
        for agent in self._ifconfig.get("agent", []):
            res += utils.dict_format(
                agent,
                '\tagent domain:{} type:{} flags:{} desc:"{}"\n',
                "domain",
                "type",
                "flag",
                "desc",
            )
        res += utils.dict_format(
            self._ifconfig.get("link_quality"), "\tlink quality: {} ({})\n", "value", "desc"
        )
        res += utils.dict_format(
            self._ifconfig.get("state_availability"),
            "\tstate availability: {} ({})\n",
            "value",
            "desc",
        )
        res += utils.dict_format(
            self._ifconfig.get("scheduler"), "\tscheduler: {} {}\n", "value", "desc"
        )
        res += self._format("\teffective interface: {}\n", "effective_interface")
        res += utils.dict_format(
            self._ifconfig.get("link_rate"), "\tlink rate: {:.2f} {}\n", "rate", "rate_um"
        )
        res += utils.dict_format(
            self._ifconfig.get("uplink_rate"),
            "\tuplink rate: {:.2f} {} [eff] / {:.2f} {}\n",
            "eff",
            "eff_um",
            "max",
            "max_um",
        )
        res += utils.dict_format(
            self._ifconfig.get("downlink_rate"),
            "\tdownlink rate: {:.2f} {} [eff] / {:.2f} {} [max]\n",
            "eff",
            "eff_um",
            "max",
            "max_um",
        )
        res += self._format("\ttimestamp: {}\n", "timestamp")
        res += utils.dict_format(
            self._ifconfig.get("qosmarking"),
            "\tqosmarking enabled: {} mode: {}\n",
            "enabled",
            "mode",
        )
        res += self._format("\tlow power mode: {}\n", "low_power_mode")
        res += self._format("\tmulti layer packet logging (mpklog): {}\n", "mpklog")
        res += self._format("\troutermode4: {}\n", "routermode4")
        res += self._format("\troutermode6: {}\n", "routermode6")
        return res.rstrip()


class _IpAddress(_Ifconfig):
    def __init__(self, interface=None, data=None, details=True):
        super().__init__(interface=interface, data=data, details=details)
        self._dump = self._data

    def _get_link(self):
        if self._ifconfig.get("peer"):
            return self._ifconfig["peer"]
        if self._ifconfig.get("vlan", {}).get("parent"):
            return self._ifconfig["vlan"]["parent"]
        return None

    def _get_master(self):
        if self._ifconfig.get("master"):
            return self._ifconfig["master"].name
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
                    "ipfilter": self._ifconfig["bridge"]["ipfilter"] != "disabled",
                }
            )
        return info_data if info_data else None

    def _get_info_slave_kind(self):
        master = self._ifconfig.get("master")
        if isinstance(master, _IfconfigBase):
            return master._get_info_kind()
        return None

    def _get_info_slave_data(self):
        master = self._ifconfig.get("master")
        if isinstance(master, _IfconfigBase):
            if master._ifconfig["interface"].startswith("bond"):
                # FIXME: where to find original hardawre lladdr?
                return {"perm_hwaddr": self._ifconfig["lladdress"]}
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
        for family in ["inet", "inet6"]:
            for inet in self._ifconfig.get(family, []):
                ip = Prefix(inet["address"])
                addr = {"family": family, "local": inet["address"]}
                if inet["peer"]:
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
                if family == "inet":
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

    @property
    def _dict(self):
        return {
            "ifindex": self._ifconfig["index"],
            "link": self._get_link(),
            "ifname": self._ifconfig["interface"],
            "flags": self._ifconfig["flags"],
            "eflags": self._ifconfig.get("eflags"),
            "xflags": self._ifconfig.get("xflags"),
            "options": self._ifconfig.get("options"),
            "capabilities": self._ifconfig.get("capabilities"),
            "hwassist": self._ifconfig.get("hwassist"),
            "mtu": self._ifconfig["mtu"],
            # "qdisc": "noqueue",
            "master": self._get_master(),
            "operstate": OPER_STATES[self._ifconfig.get("status", "none")],
            "group": "default",
            "txqlen": _TXQLEN,
            "link_type": self._ifconfig.get("link_type", "none"),
            "address": self._ifconfig.get("lladdress"),
            "link_pointtopoint": True if "POINTOPOINT" in self._ifconfig["flags"] else None,
            "broadcast": self._ifconfig.get("llbroadcast"),
            # TODO:
            # "promiscuity": 0,
            # "min_mtu": 0,
            # "max_mtu": 0,
            "linkinfo": self._get_linkinfo(),
            # TODO:
            # "num_tx_queues": 1,
            # "num_rx_queues": 1,
            # "gso_max_size": 65536,
            # "gso_max_segs": 65535,
            "addr_info": self._get_addr_info(),
        }

    def str(self, details=None):
        if details is None:
            details = self._details
        res = self._format("{}: {}", "ifindex", "ifname")
        res += self._format("@{}", "link")
        res += f": <{','.join(self['flags'])}> mtu {self['mtu']}"
        res += self._format(" master {}", "master")
        res += self._format(" state {}", "operstate")
        res += self._format(" qlen {}", "txqlen")
        res += "\n"

        res += self._format("    link/{}", "link_type")
        res += self._format(" {}", "address")
        res += self._format(" brd {}", "broadcast")
        res += self._format(" minmtu {}", "min_mtu")
        res += self._format(" maxmtu {}", "max_mtu")
        res += self._format(" numtxqueues {}", "num_tx_queues")
        res += self._format(" numrxqueues {}", "num_rx_queues")
        res += self._format(" gso_max_size {}", "gso_max_size")
        res += self._format(" gso_max_segs {}", "gso_max_segs")
        res += "\n"

        if self.visible("linkinfo", details=details) and self["linkinfo"].get("info_kind"):
            info = self["linkinfo"]
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
        for addr in self.get("addr_info", []):
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


class _IpLink(_IpAddress):
    def _get_addr_info(self):
        return []


class Ifconfig:
    """
    Collection of interfaces with dual representation ifconfig/iproute2
    """

    __slots__ = ("_interfaces", "_kind")

    def __init__(self, kind=None, details=True):
        if kind:
            if isinstance(kind, type) and not issubclass(kind, _Ifconfig):
                raise ValueError("kind must be a subtype of <class '_Ifconfig'>")
            self._kind = kind
        else:
            self._kind = _Ifconfig
        self._interfaces = []
        res = utils.shell(_IFCONFIG, "-f", "inet:cidr,inet6:cidr", "-a", "-L", "-m", "-v")
        for data in re.findall(rf"(^{IFNAME}:.*\n(?:\t.*[\n|$])*)", res, flags=re.MULTILINE):
            # for every single interface:
            self._interfaces.append(self._kind(data=data, details=details))
        self._link_interfaces()

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
            isinstance(i, self._kind) for i in interfaces
        ):
            raise ValueError(f"argument is not list() of <class '{self._kind.__name__}'>")
        self._interfaces = interfaces

    def _link_interfaces(self):
        """
        Look up for bond/bridge interface relations
        """
        for interface in self._interfaces:
            for index, slave in enumerate(interface._ifconfig.get("bond", [])):
                if isinstance(slave, str):
                    slave = self.lookup("interface", slave)
                    interface._ifconfig["bond"][index] = slave
                slave._ifconfig["master"] = interface
            if interface._ifconfig.get("bridge"):
                for member in interface._ifconfig["bridge"].get("member", []):
                    slave = member["interface"]
                    if isinstance(slave, str):
                        slave = self.lookup("interface", slave)
                        member["interface"] = slave
                    slave._ifconfig["master"] = interface
        for interface in self._interfaces:
            interface.__update__()

    def lookup(self, key, value):
        """
        Lookup for element in list with list[ley] == value
        """
        return next((i for i in self._interfaces if i._ifconfig.get(key) == value), None)

    def exist(self, interface):
        return any(i.name == interface for i in self._interfaces)

    def dict(self, details=None):
        return [interface.dict(details=details) for interface in self._interfaces]

    # alias self.list() as self.dict()
    list = dict

    def str(self, details=None):
        return "\n".join([interface.str(details=details) for interface in self._interfaces])

    @property
    def interfaces(self):
        return self._interfaces

    @property
    def details(self):
        return self._interfaces[0].detail

    @details.setter
    def details(self, value):
        for interface in self._interfaces:
            interface.details = value


class IpAddress(Ifconfig):
    def __init__(self, details=True):
        super().__init__(kind=_IpAddress, details=details)


class IpLink(Ifconfig):
    def __init__(self, details=True):
        super().__init__(kind=_IpLink, details=details)
