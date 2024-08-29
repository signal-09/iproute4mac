import iproute4mac.libc as libc

from iproute4mac.utils import *


_IFCONFIG = "ifconfig"

_SYSCTL_RXQLEN = "net.link.generic.system.rcvq_maxlen"
_SYSCTL_TXQLEN = "net.link.generic.system.sndq_maxlen"
_TXQLEN = libc.sysctl(_SYSCTL_TXQLEN)

# nu <netinet6/nd6.h>
_ND6_INFINITE_LIFETIME = 0xFFFFFFFF

_DETAIL_FIELDS = [
    "eflags",
    "xflags",
    "options",
    "capabilities",
    "hwassist",
    "bridge",
    "promiscuity",
    "min_mtu",
    "max_mtu",
    "linkinfo",
    "num_tx_queues",
    "num_rx_queues",
    "gso_max_size",
    "gso_max_segs",
]


# https://opensource.apple.com/source/network_cmds/network_cmds-606.40.2/ifconfig.tproj/ifconfig.c.auto.html


def run(*argv, fatal=True):
    return shell(_IFCONFIG, *argv, fatal=fatal)


class _Ifconfig:
    """
    Basic interface dictionary representation of macOS ifconfig output
    """

    __slots__ = ("_properties", "_header", "_data")

    def __init__(self, properties, header):
        if not isinstance(properties, dict):
            raise ValueError(f"properties ({type(properties)}) is not <class 'dict'>")
        if header not in properties:
            raise ValueError(f"field '{header}' not present in properties dict")
        self._properties = properties
        self._header = header
        self._data = {}
        for key in self._properties:
            if self._properties[key]:
                self._data.update(self._decode(key))

    @staticmethod
    def _groupdict(entry):
        """
        Expand groupdict() with list and numbers
        """
        res = entry.groupdict()
        for key, value in res.items():
            if key == "flags":
                res[key] = value.split(",") if value else []
            if value is None:
                continue
            if value.isdigit():
                res[key] = int(value)
            elif value.replace(".", "", 1).isdigit():
                res[key] = float(value)
            elif value.startswith("<") and value.endswith(">"):
                # <unknown type> and <none>
                res[key] = None
        return res

    def _decode(self, entry):
        if self._properties.get(entry) is None:
            res = None
        elif isinstance(self._properties[entry], _Ifconfig):
            res = self._properties[entry]._data
        elif hasattr(self._properties[entry], "__iter__"):
            res = [self._groupdict(e) for e in self._properties[entry]]
        elif len(res := self._groupdict(self._properties[entry])) == 1:
            res = res[next(iter(res))]
        return {entry: res} if entry != self._header else res

    def dict(self):
        return self._data


class _BridgeRegEx(_Ifconfig):
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
        rf"\tmember: (?P<interface>{IFNAME}) flags=\w+<(?P<flags>.*)>\n"
        r"\t\s+ifmaxaddr (?P<ifmaxaddr>\d+) port (?P<port>\d+) priority (?P<priority>\d+) path cost (?P<cost>\d+)\n"
        rf"\t\s+hostfilter (?P<hostfilter>\d+) hw: (?P<hw>{LLADDR}) ip: (?P<ip>{IPV4ADDR}|{IPV6ADDR})"
    )

    def __init__(self, data):
        properties = {"bridge": self._bridge.search(data), "member": self._member.finditer(data)}
        super().__init__(properties, "bridge")


class _IfconfigRegEx(_Ifconfig):
    """
    Specific interface dictionary representation of macOS ifconfig output
    """

    _interface = re.compile(
        r"(?P<interface>\w+): flags=\w+<(?P<flags>.*)>"
        r" mtu (?P<mtu>\d+)?"
        r"(?: rtref (?P<rtref>\d+))?"
        r" index (?P<index>\d+)"
    )
    _eflags = re.compile(r"\teflags=\w+<(?P<flags>.*)>")
    _xflags = re.compile(r"\txflags=\w+<(?P<flags>.*)>")
    _options = re.compile(r"\toptions=\w+<(?P<flags>.*)>")
    _capabilities = re.compile(r"\tcapabilities=\w+<(?P<flags>.*)>")
    _hwassist = re.compile(r"\thwassist=\w+<(?P<flags>.*)>")
    _ether = re.compile(rf"\tether (?P<ether>{LLADDR})")
    _bridge = re.compile(r"\tConfiguration:\n(?:\t\t.*\n)+(?:\tmember: .*\n(?:\t\s+.*\n)+)*")
    _peer = re.compile(r"\s+peer: (?P<peer>\w+)")
    _inet = re.compile(
        rf"\tinet (?P<address>{IPV4ADDR})"
        rf"(?: --> (?P<peer>{IPV4ADDR}))?"
        rf" netmask (?P<netmask>{IPV4MASK})"
        rf"(?: broadcast (?P<broadcast>{IPV4ADDR}))?"
    )
    _inet6 = re.compile(
        rf"\tinet6 (?P<address>{IPV6ADDR})(?:%\w+)?"
        rf"(?: --> (?P<peer>{IPV6ADDR})(?:%\w+)?)?"
        r" prefixlen (?P<prefixlen>\d+)"
        r"(?: (?P<autoconf>autoconf))?"
        r"(?: (?P<secured>secured))?"
        r"(?: pltime (?P<pltime>\d+))?"
        r"(?: vltime (?P<vltime>\d+))?"
        r"(?: scopeid (?P<scopeid>0x[0-9a-fA-F]+))?"
    )
    _vlan = re.compile(rf"\s+vlan: (?P<vlanid>\d+) parent interface: (?P<parent>\<none\>|{IFNAME})")
    _netif = re.compile(rf"\tnetif: {NETIF}")
    _flowswitch = re.compile(rf"\tflowswitch: {NETIF}")
    _nd6_options = re.compile(r"\tnd6 options=\w+<(?P<flags>.*)>")
    _status = re.compile(r"\tstatus: (?P<status>\w+)")
    _media = re.compile(r"\tmedia: (?P<media>.+)")
    _supported_media = re.compile(r"\tsupported media:")
    _media_supported = re.compile(r"\t\t(?:media (?P<media>\w+)(?: mediaopt (?P<mediaopt>[\w-]+))?|<unknown type>)")
    _bond = re.compile(rf"\s+bond interfaces: (?P<list>{IFNAME}(?: {IFNAME}+)*)")
    _generation_id = re.compile(r"\tgeneration id: (?P<generation_id>\d+)")
    _type = re.compile(r"\ttype: (?P<type>[\w ]+)")
    _agent = re.compile(r'\tagent domain:(?P<domain>\w+) type:(?P<type>\w+) flags:(?P<flag>0x[0-9a-fA-F]+) desc:"(?P<desc>.*)"')
    _link_quality = re.compile(r"\tlink quality: (?P<quality>\d+)")
    _state_availability = re.compile(r"\tstate availability: (?P<availability>\d+)")
    _scheduler = re.compile(r"\tscheduler: (?P<scheduler>\w+)")
    _effective_interface = re.compile(rf"\teffective interface: (?P<interface>{IFNAME})")
    _uplink_rate = re.compile(r"\tuplink rate: (?P<eff>[\d\.]+) (?P<eff_um>\w+) \[eff\] / (?P<max>[\d\.]+) (?P<max_um>\w+)")
    _downlink_rate = re.compile(r"\tdownlink rate: (?P<eff>[\d\.]+) (?P<eff_um>\w+) \[eff\] / (?P<max>[\d\.]+) (?P<max_um>\w+)")
    _tqosmarking = re.compile(r"\tqosmarking enabled: (?P<enabled>\w+) mode: (?P<mode>\w+)")
    _low_power_mode = re.compile(r"\tlow power mode: (?P<mode>\w+)")
    _mpklog = re.compile(r"\tmulti layer packet logging \(mpklog\): (?P<mode>\w+)")
    _routermode4 = re.compile(r"\troutermode4: (?P<mode>\w+)")
    _routermode6 = re.compile(r"\troutermode6: (?P<mode>\w+)")

    def __init__(self, data):
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
            "status": self._status.search(data),
            "media": self._media.search(data),
            "supported_media": self._supported_media.search(data),
            "media_supported": self._media_supported.finditer(data),
            "bond": self._bond.search(data),
            "generation_id": self._generation_id.search(data),
            "type": self._type.search(data),
            "agent": self._agent.finditer(data),
            "link_quality": self._link_quality.search(data),
            "state_availability": self._state_availability.search(data),
            "scheduler": self._scheduler.search(data),
            "effective_interface": self._effective_interface.search(data),
            "uplink_rate": self._uplink_rate.search(data),
            "downlink_rate": self._downlink_rate.search(data),
            "tqosmarking": self._tqosmarking.search(data),
            "low_power_mode": self._low_power_mode.search(data),
            "mpklog": self._mpklog.search(data),
            "routermode4": self._routermode4.search(data),
            "routermode6": self._routermode6.search(data),
        }
        super().__init__(properties, "interface")

    @property
    def name(self):
        return self._data.get(self._header)

    @property
    def index(self):
        return self._data.get("index")

    def _search_bridge(self, data):
        """
        Adding bridge data
        """
        if res := self._bridge.search(data):
            return _BridgeRegEx(res.group())
        return None


class _Iproute2:
    """
    iproute2 representation of single interface

    Input: _Ifconfig dict data
    """

    __slots__ = "_link"

    def __init__(self, link):
        self._link = {
            "ifindex": link["index"],
            "link": link.get("peer"),
            "ifname": link["interface"],
            "flags": link["flags"],
            "eflags": link.get("eflags"),
            "xflags": link.get("xflags"),
            "options": link.get("options"),
            "capabilities": link.get("capabilities"),
            "hwassist": link.get("hwassist"),
            "mtu": link["mtu"],
            # "qdisc": "noqueue",
            "master": None,
            "operstate": OPER_STATES[link["status"]] if "status" in link else "UNKNOWN",
            "group": "default",
            "txqlen": _TXQLEN,
            "link_type": "none",
            "address": link["ether"] if "ether" in link else None,
            "broadcast": "ff:ff:ff:ff:ff:ff" if "ether" in link else None,
            # "promiscuity": 0,
            # "min_mtu": 0,
            # "max_mtu": 0,
            "link_info": None,
            # "num_tx_queues": 1,
            # "num_rx_queues": 1,
            # "gso_max_size": 65536,
            # "gso_max_segs": 65535,
            "addr_info": [],
        }
        if "LOOPBACK" in link["flags"]:
            self._link["link_type"] = "loopback"
            self._link["address"] = "00:00:00:00:00:00"
            self._link["broadcast"] = "00:00:00:00:00:00"
        elif self._present(link, "ether"):
            self._link["link_type"] = "ether"
        if "POINTOPOINT" in link["flags"]:
            self._link["link_pointtopoint"] = True
        if startwith(link["interface"], "bridge", "bond", "feth", "vlan"):
            self._link["linkinfo"] = {"info_kind": re.sub("[0-9]+", "", link["interface"])}
            if self._present(link, "vlan"):
                self._link["linkinfo"]["info_data"] = {"protocol": "802.1Q", "id": link["vlan"]["vlanid"], "flags": []}
                self._link["link"] = link["vlan"]["parent"]
        for family in ["inet", "inet6"]:
            for inet in link[family]:
                ip = Prefix(inet["address"])
                addr = {"family": family, "local": inet["address"]}
                if inet["peer"]:
                    addr["address"] = inet["peer"]
                if self._present(inet, "prefixlen"):
                    addr["prefixlen"] = inet["prefixlen"]
                if self._present(inet, "netmask"):
                    addr["prefixlen"] = netmask_to_length(inet["netmask"])
                if self._present(inet, "broadcast"):
                    addr["broadcast"] = inet["broadcast"]
                if ip.is_link:
                    addr["scope"] = "link"
                elif ip.is_global:
                    # NOTE: may be Python ipaddress is_global() is not compliant with iproute2
                    addr["scope"] = "global"
                else:
                    addr["scope"] = "host"
                if family == "inet":
                    addr["label"] = link["interface"]
                addr["valid_life_time"] = inet["vltime"] if inet.get("vltime") is not None else _ND6_INFINITE_LIFETIME
                addr["preferred_life_time"] = inet["pltime"] if inet.get("pltime") is not None else _ND6_INFINITE_LIFETIME
                # TODO:
                # "dynamic": true,
                # "mngtmpaddr": true
                # "noprefixroute": true
                self._link["addr_info"].append(addr)

    def __getitem__(self, key):
        return self._link.get(key)

    def __setitem__(self, key, value):
        self._link[key] = value

    def __delitem__(self, key):
        if self._present(self._link, key):
            del self._link[key]

    def __contains__(self, other):
        return other in self._link

    @staticmethod
    def _present(data, key, value=None):
        if key in data:
            if value is None:
                return data[key] is not None
            else:
                return data[key] == value
        else:
            for k, v in data.items():
                if v is not None and isinstance(v, dict):
                    return _Iproute2._present(v, key, value=value)
        return False

    def present(self, key, value=None):
        return self._present(self._link, key, value=value)

    def get(self, key, value=None):
        return self._link.get(key, value)

    def pop(self, key, value=None):
        if value is None:
            return self._link.pop(key)
        return self._link.pop(key, value)

    def dict(self, details=True):
        """
        JSON iproute2 output represented by a dictionary
        """
        return {k: v for k, v in self._link.items() if v is not None and (details or k not in _DETAIL_FIELDS)}

    def str(self, details=True):
        """
        Standard iproute2 output
        """
        link = self.dict(details=details)
        res = str(link["ifindex"]) + ": " + link["ifname"]
        if "link" in link:
            res += "@" + self["link"]
        res += ": <" + ",".join(self["flags"]) + "> mtu " + str(self["mtu"])
        if "master" in link:
            res += " master " + self["master"]
        if "operstate" in link:
            res += " state " + self["operstate"]
        if "txqlen" in link:
            res += " qlen " + str(self["txqlen"])
        res += "\n"

        res += "    link/" + self["link_type"]
        if "address" in link:
            res += " " + self["address"]
        if "broadcast" in link:
            res += " brd " + self["broadcast"]
        if "promiscuity" in link:
            res += " promiscuity " + str(self["promiscuity"])
        if "min_mtu" in link:
            res += " minmtu " + str(self["min_mtu"])
        if "max_mtu" in link:
            res += " maxmtu " + str(self["max_mtu"])
        if "num_tx_queues" in link:
            res += " numtxqueues " + str(self["num_tx_queues"])
        if "num_rx_queues" in link:
            res += " numrxqueues " + str(self["num_rx_queues"])
        if "gso_max_size" in link:
            res += " gso_max_size " + str(self["gso_max_size"])
        if "gso_max_segs" in link:
            res += " gso_max_segs " + str(self["gso_max_segs"])
        res += "\n"

        if "linkinfo" in link and "info_kind" in link["linkinfo"]:
            info = link["linkinfo"]
            res += "    " + info["info_kind"]
            if info["info_kind"] == "vlan":
                data = info["info_data"]
                res += " protocol " + data["protocol"] + " id " + str(data["id"])
            elif info["info_kind"] == "bridge":
                data = info["info_data"]
                res += " " + " ".join([f"{key} {value}" for key, value in data.items()])
            res += "\n"

        ips = []
        for addr in link.get("addr_info", []):
            if addr["family"] == "inet" and addr["prefixlen"] < 32:
                local = Prefix(f'{addr["local"]}/{addr["prefixlen"]}')
                secondary = any(local in ip for ip in ips)
                ips.append(local)
            else:
                secondary = False
            res += "    " + addr["family"]
            res += " " + addr["local"]
            if "address" in addr:
                res += " peer " + addr["address"]
            res += "/" + str(addr["prefixlen"])
            if "broadcast" in addr:
                res += " brd " + addr["broadcast"]
            if "scope" in addr:
                res += " scope " + addr["scope"]
            # TODO: print "secondary" if ...
            if secondary:
                res += " secondary"
            if "label" in addr:
                res += " " + addr["label"]
            res += "\n"
            if "valid_life_time" in addr and "preferred_life_time" in addr:
                res += (
                    "       valid_lft "
                    + ("forever" if addr["valid_life_time"] == _ND6_INFINITE_LIFETIME else str(addr["valid_life_time"]))
                    + " preferred_lft "
                    + ("forever" if addr["preferred_life_time"] == _ND6_INFINITE_LIFETIME else str(addr["preferred_life_time"]))
                )
                res += "\n"

        return res

    @property
    def ifname(self):
        return self._link.get("ifname")

    @property
    def ifindex(self):
        return self._link.get("ifindex")


class Ifconfig:
    """
    Collection of interfaces with dual representation ifconfig/iproute2
    """

    __slots__ = ("_interfaces", "_links")

    def __init__(self):
        self._interfaces = []
        res = shell(_IFCONFIG, "-a", "-L", "-m", "-r", "-v")
        for data in re.findall(rf"(^{IFNAME}:.*\n(?:\t.*[\n|$])*)", res, flags=re.MULTILINE):
            # for every single interface:
            self._interfaces.append(_IfconfigRegEx(data))
        self._init_data()
        self._parse_data()

    def __len__(self):
        return len(self._links)

    def __getitem__(self, index):
        return self._links[index]

    def pop(self, index=-1):
        return self._links.pop(index)

    def set(self, links):
        if not isinstance(links, list) or not all(isinstance(l, _Iproute2) for l in links):
            raise ValueError("argument is not list() of <class 'ifconfig._IProute2'>")
        self._links = links

    def _init_data(self):
        """
        Create iproute2 basic data structure from ifconfig dictionaries
        """
        self._links = []
        for interface in self._interfaces:
            self._links.append(_Iproute2(interface._data))

    def _parse_data(self):
        """
        Decorate iproute2 data structure with interface relations
        """
        for interface in self._interfaces:
            if slaves := interface._data.get("bond"):
                for ifname in slaves.split():
                    slave = self._find(self._links, "ifname", ifname)
                    slave["master"] = interface.name
                    slave["linkinfo"] = slave.get("linkinfo", {})
                    slave["linkinfo"].update(
                        {
                            "info_slave_kind": "bond",
                            # FIXME: where to find hardawre lladdr?
                            "perm_hwaddr": slave["address"],
                        }
                    )
            if bridge := interface._data.get("bridge"):
                master = self._find(self._links, "ifname", interface.name)
                master["linkinfo"] = master.get("linkinfo", {})
                master["linkinfo"]["info_data"] = master["linkinfo"].get("info_data", {})
                master["linkinfo"]["info_data"].update(
                    {
                        "forward_delay": bridge["fwddelay"],
                        "hello_time": bridge["hellotime"],
                        "max_age": bridge["maxage"],
                        "ageing_time": bridge["timeout"],
                        # "stp_state": 0,
                        "priority": bridge["root_priority"],
                        # "vlan_filtering": 0,
                        # "vlan_protocol": "802.1Q",
                        "bridge_id": bridge["id"],
                        "root_id": bridge["root_id"],
                        "root_port": bridge["root_port"],
                        "root_path_cost": bridge["root_cost"],
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
                        "ipfilter": bridge["ipfilter"] != "disabled",
                    }
                )
                master = self._find(self._links, "ifname", interface.name)
                for member in bridge["member"]:
                    slave = self._find(self._links, "ifname", member["interface"])
                    slave["master"] = interface.name
                    slave["linkinfo"] = slave.get("linkinfo", {})
                    slave["linkinfo"].update({"info_slave_kind": "bridge"})

    @staticmethod
    def _find(data, key, value):
        """
        Lookup for element in list with list[ley] == value
        """
        return next((l for l in data if l.get(key) == value), None)

    def ifconfig(self, index):
        """
        Retrieve ifconfig interface dictionary by ifname or ifindex
        """
        if isinstance(index, str):
            return next((i.dict() for i in self._interfaces if i.name == index), None)
        elif isinstance(index, int):
            return next((i.dict() for i in self._interfaces if i.index == index), None)
        return None

    def iproute2(self, index):
        """
        Retrieve iproute2 interface dictionary by ifname or ifindex
        """
        if isinstance(index, str):
            return next((i.dict() for i in self._links if i.ifname == index), None)
        elif isinstance(index, int):
            return next((i.dict() for i in self._links if i.ifindex == index), None)
        return None

    def exist(self, interface):
        return any(i.name == interface for i in self._interfaces)

    def list(self):
        """
        List interface names
        """
        return [i.name for i in self._interfaces]

    def dict(self, details=True):
        """
        List interface dictiornaries
        """
        return [i.dict(details=details) for i in self._links]

    def str(self, details=True):
        res = ""
        for i in self._links:
            res += i.str(details=details)
        return res
