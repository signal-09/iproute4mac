import re

from iproute4mac.utils import *


def exec(*argv):
    return shell("ifconfig", *argv)


def dumps(links, option):
    if option["json"]:
        print(json_dumps(links, option["pretty"]))
        return

    if not links:
        return

    for link in links:
        stdout(link["ifindex"], ": ", link["ifname"])
        if "link" in link:
            stdout("@", link["link"])
        stdout(": <", ",".join(link["flags"]), "> mtu ", link["mtu"])
        if "master" in link:
            stdout(" master ", link["master"])
        stdout(" state ", link["operstate"], end="\n")

        stdout("    link/", link["link_type"])
        if "address" in link:
            stdout(" ", link["address"])
        if "broadcast" in link:
            stdout(" brd ", link["broadcast"])
        stdout(end="\n")

        if "linkinfo" in link and "info_kind" in link["linkinfo"]:
            info = link["linkinfo"]
            if info["info_kind"] == "vlan":
                data = info["info_data"]
                stdout(
                    "    ",
                    info["info_kind"],
                    " protocol ",
                    data["protocol"],
                    " id ",
                    data["id"],
                    end="\n",
                )
            elif info["info_kind"] == "bridge":
                data = info["info_data"]
                stdout(
                    "    bridge ",
                    " ".join([f"{key} {value}" for key, value in data.items()]),
                    end="\n",
                )

        for addr in link.get("addr_info", []):
            stdout("    ", addr["family"])
            stdout(" ", addr["local"])
            if "address" in addr:
                stdout(" peer ", addr["address"])
            stdout("/", addr["prefixlen"])
            if "broadcast" in addr:
                stdout(" brd ", addr["broadcast"])
            if "scope" in addr:
                stdout(" scope ", addr["scope"])
            stdout(end="\n")
            if "valid_life_time" in addr and "preferred_life_time" in addr:
                stdout(
                    "       valid_lft ",
                    "forever" if addr["valid_life_time"] == ND6_INFINITE_LIFETIME else addr["valid_life_time"],
                    " preferred_lft ",
                    "forever" if addr["preferred_life_time"] == ND6_INFINITE_LIFETIME else addr["preferred_life_time"],
                )
                stdout(end="\n")


class ifconfigRegEx:
    _header = re.compile(r"(?P<ifname>\w+):" r" flags=\w+<(?P<flags>.*)>" r" mtu (?P<mtu>\d+)" r" index (?P<ifindex>\d+)")
    _eflags = re.compile(r"\s+eflags=\w+<(?P<eflags>.*)>")
    _ether = re.compile(rf"\s+ether (?P<ether>{LLADDR})")
    _inet = re.compile(
        rf"\s+inet (?P<local>{IPV4ADDR})"
        rf"(?: --> (?P<address>{IPV4ADDR}))?"
        rf" netmask (?P<netmask>{IPV4MASK})"
        rf"(?: broadcast (?P<broadcast>{IPV4ADDR}))?"
    )
    _inet6 = re.compile(
        rf"\s+inet6 (?P<local>{IPV6ADDR})(?:%\w+)?"
        r" prefixlen (?P<prefixlen>\d+)"
        r"(?: (?P<autoconf>autoconf))?"
        r"(?: (?P<secured>secured))?"
        r"(?: pltime (?P<pltime>\d+))?"
        r"(?: vltime (?P<vltime>\d+))?"
        r"(?: scopeid (?P<scopeid>0x[0-9a-fA-F]+))?"
    )
    _state = re.compile(r"\s+status: (?P<state>\w+)")
    _vlan = re.compile(r"\s+vlan: (?P<vlanid>\d+) parent interface: (?P<parent><?\w+>?)")
    _bond = re.compile(r"\s+bond interfaces: (\w+(?: \w+)*)")
    _bridge = re.compile(r"\s+Configuration:")

    def __init__(self, line):
        self.header = self._header.match(line)
        self.eflags = self._eflags.match(line)
        self.ether = self._ether.match(line)
        self.inet = self._inet.match(line)
        self.inet6 = self._inet6.match(line)
        self.state = self._state.match(line)
        self.vlan = self._vlan.match(line)
        self.bond = self._bond.match(line)
        self.bridge = self._bridge.match(line)


class bridgeRegEx:
    _id = re.compile(
        r"\s+id (?P<id>(?:[0-9a-fA-F]{1,2}:?){6})"
        r" priority (?P<priority>\d+)"
        r" hellotime (?P<hello>\d+)"
        r" fwddelay (?P<delay>\d+)"
    )
    _age = re.compile(
        r"\s+maxage (?P<max_age>\d+)"
        r" holdcnt (?P<hold>\d+)"
        r" proto (?P<protocol>\w+)"
        r" maxaddr (?P<addr>\d+)"
        r" timeout (?P<ageing>\d+)"
    )
    _root = re.compile(
        r"\s+root id (?P<id>(?:[0-9a-fA-F]{1,2}:?){6})"
        r" priority (?P<priority>\d+)"
        r" ifcost (?P<cost>\d+)"
        r" port (?P<port>\d+)"
    )
    _filter = re.compile(r"\s+ipfilter (?P<filter>\w+)" r" flags (?P<flags>0x[0-9a-fA-F]+)")
    _member = re.compile(r"\s+member: (?P<member>\w+)")
    _cache = re.compile(r"\s+media:")

    def __init__(self, line):
        self.id = self._id.match(line)
        self.age = self._age.match(line)
        self.root = self._root.match(line)
        self.filter = self._filter.match(line)
        self.member = self._member.match(line)
        self.cache = self._cache.match(line)


def parse_bridge(lines, links, link):
    info_data = {}
    while line := next(lines):
        match = bridgeRegEx(line)

        if match.id:
            info_data["forward_delay"] = int(match.id.group("delay"))
            info_data["hello_time"] = int(match.id.group("hello"))
        elif match.age:
            info_data["max_age"] = int(match.age.group("max_age"))
            info_data["ageing_time"] = int(match.age.group("ageing"))
        elif match.root:
            info_data["priority"] = int(match.root.group("priority"))
            info_data["root_id"] = match.root.group("id")
            info_data["root_port"] = int(match.root.group("port"))
            info_data["root_path_cost"] = int(match.root.group("cost"))
        elif match.filter:
            info_data["ipfilter"] = match.filter.group("filter") != "disabled"
        elif match.member:
            slave = next(item for item in links if item["ifname"] == match.member.group("member"))
            slave["master"] = link["ifname"]
            slave["linkinfo"] = {"info_slave_kind": "bridge"}
        elif match.cache:
            link["linkinfo"].update({"info_data": info_data})
            break


def parse(res, option):
    links = []
    lines = iter(res.split("\n"))
    while line := next(lines):
        match = ifconfigRegEx(line)

        if match.header:
            header = match.header.groupdict()
            link = {
                "ifindex": int(header["ifindex"]),
                "ifname": header["ifname"],
                "flags": header["flags"].split(",") if header["flags"] != "" else [],
                "mtu": int(header["mtu"]),
                "operstate": "UNKNOWN",
                "link_type": "none",
            }

            if "LOOPBACK" in link["flags"]:
                link["link_type"] = "loopback"
                link["address"] = "00:00:00:00:00:00"
                link["broadcast"] = "00:00:00:00:00:00"
            elif "POINTOPOINT" in link["flags"]:
                link["link_pointtopoint"] = True

            if startwith(link["ifname"], "bridge", "bond", "vlan"):
                link["linkinfo"] = {"info_kind": re.sub(r"[0-9]+", "", link["ifname"])}

            links.append(link)
            inet_count = 0
            inet6_count = 0
            continue

        if match.eflags:
            link["eflags"] = match.eflags.group("eflags").split(",")
        elif match.ether:
            link["link_type"] = "ether"
            link["address"] = match.ether.group("ether")
            link["broadcast"] = "ff:ff:ff:ff:ff:ff"
        elif match.state:
            link["operstate"] = oper_states[match.state.group("state")]
        elif match.inet and option["preferred_family"] in (AF_INET, AF_UNSPEC):
            inet = match.inet.groupdict()
            addr = {"family": "inet", "local": inet["local"]}
            if inet["address"]:
                addr["address"] = inet["address"]
            addr["prefixlen"] = netmask_to_length(inet["netmask"])
            if inet["broadcast"]:
                addr["broadcast"] = inet["broadcast"]
            ip = Prefix(addr["local"])
            if ip.is_link:
                addr["scope"] = "link"
            elif ip.is_global:
                # FIXME: may be Python ipaddress is_global() not compliant with iproute2
                addr["scope"] = "global"
            else:
                addr["scope"] = "host"
            addr.update(
                {
                    "valid_life_time": ND6_INFINITE_LIFETIME,
                    "preferred_life_time": ND6_INFINITE_LIFETIME,
                }
            )
            if inet_count + inet6_count > 0:
                # Let IPv4 at beginning
                link["addr_info"].insert(inet_count, addr)
            else:
                link["addr_info"] = [addr]
            inet_count += 1
        elif match.inet6 and option["preferred_family"] in (AF_INET6, AF_UNSPEC):
            inet6 = match.inet6.groupdict()
            ip = Prefix(inet6["local"])
            if ip.is_link:
                scope = "link"
            elif ip.is_global:
                # FIXME: may be Python ipaddress is_global() not compliant with iproute2
                scope = "global"
            else:
                scope = "host"
            addr = {
                "family": "inet6",
                "local": inet6["local"],
                "prefixlen": int(inet6["prefixlen"]),
                "scope": scope,
                "valid_life_time": int(inet6["vltime"]) if inet6["vltime"] else ND6_INFINITE_LIFETIME,
                "preferred_life_time": int(inet6["pltime"]) if inet6["pltime"] else ND6_INFINITE_LIFETIME,
            }
            if inet_count + inet6_count > 0:
                # Put IPv6 after IPv4
                link["addr_info"].append(addr)
            else:
                link["addr_info"] = [addr]
            inet6_count += 1
        elif match.vlan:
            parent = match.vlan.group("parent")
            if parent != "<none>":
                link["link"] = parent
            link["linkinfo"].update(
                {
                    "info_data": {
                        "protocol": "802.1Q",
                        "id": int(match.vlan.group("vlanid")),
                        "flags": [],
                    }
                }
            )
        elif match.bond:
            for ifname in match.bond.group(1).split(" "):
                slave = next(item for item in links if item["ifname"] == ifname)
                slave["master"] = link["ifname"]
                slave["address"] = link["address"]
                slave["linkinfo"] = {
                    "info_slave_kind": "bond",
                    "perm_hwaddr": slave["address"],
                }
        elif match.bridge:
            parse_bridge(lines, links, link)

    return links
