import iproute4mac.ifconfig as ifconfig

from iproute4mac.utils import *


_NETSTAT = "netstat"
_ROUTE = "route"

# https://docs.freebsd.org/en/books/handbook/advanced-networking/#routeflags
_RTF_PROTO1 = "1"  # Protocol specific routing flag #1
_RTF_PROTO2 = "2"  # Protocol specific routing flag #2
_RTF_PROTO3 = "3"  # Protocol specific routing flag #3
_RTF_BLACKHOLE = "B"  # Just discard packets (during updates)
_RTF_BROADCAST = "b"  # The route represents a broadcast address
_RTF_CLONING = "C"  # Generate new routes on use
_RTF_PRCLONING = "c"  # Protocol-specified generate new routes on use
_RTF_DYNAMIC = "D"  # Created dynamically (by redirect)
_RTF_GATEWAY = "G"  # Destination requires forwarding by intermediary
_RTF_HOST = "H"  # Host entry (net otherwise)
_RTF_IFSCOPE = "I"  # Route is associated with an interface scope
_RTF_IFREF = "i"  # Route is holding a reference to the interface
_RTF_LLINFO = "L"  # Valid protocol to link address translation
_RTF_MODIFIED = "M"  # Modified dynamically (by redirect)
_RTF_MULTICAST = "m"  # The route represents a multicast address
_RTF_REJECT = "R"  # Host or net unreachable
_RTF_ROUTER = "r"  # Host is a default router
_RTF_STATIC = "S"  # Manually added
_RTF_UP = "U"  # Route usable
_RTF_WASCLONED = "W"  # Route was generated as a result of cloning
_RTF_XRESOLVE = "X"  # External daemon translates proto to link address
_RTF_PROXY = "Y"  # Proxying; cloned routes will not be scoped
_RTF_GLOBAL = "g"  # Route to a destination of the global internet (policy hint)

_NETSTAT_DETAIL_FIELDS = ["expire"]

_ROUTE_DUMP_MAGIC = 0x45311224

_RTN_UNSPEC = 0
_RTN_UNICAST = 1
_RTN_LOCAL = 2
_RTN_BROADCAST = 3
_RTN_ANYCAST = 4
_RTN_MULTICAST = 5
_RTN_BLACKHOLE = 6
_RTN_UNREACHABLE = 7
_RTN_PROHIBIT = 8
_RTN_THROW = 9
_RTN_NAT = 10
_RTN_XRESOLVE = 11
__RTN_MAX = 12

_RTN_MAP = (
    "none",
    "unicast",
    "local",
    "broadcast",
    "anycast",
    "multicast",
    "blackhole",
    "unreachable",
    "prohibit",
    "throw",
    "nat",
    "xresolve",
)

_ROUTE_GET_DETAIL_FIELDS = ["metrics", "table"]


def run(*argv, fatal=True):
    return shell(_ROUTE, *argv, fatal=fatal)


def get_rtn(name):
    if name.isdigit():
        rtn = int(name)
    else:
        rtn = _RTN_MAP.index(name)
    if not 0 < rtn < 2**8:
        raise ValueError
    return rtn


def is_rtn(name):
    try:
        get_rtn(name)
    except ValueError:
        return False
    return True


class _Route:
    __slots = "_route"

    def __init__(self, dst, prefix, gateway, flags, dev, expire, src):
        # address type
        if _RTF_BLACKHOLE in flags:
            addr_type = "blackhole"
            gateway = None
            dev = None
            src = None
        elif _RTF_BROADCAST in flags:
            addr_type = "broadcast"
        elif _RTF_MULTICAST in flags:
            addr_type = "multicast"
        else:
            addr_type = "unicast"

        # scope
        scope = "link"
        if gateway and re.match(LLADDR, gateway):
            pass
        elif gateway and (gateway.startswith("link#") or gateway == dev):
            gateway = None
        elif _RTF_BLACKHOLE in flags:
            scope = "global"
        elif _RTF_HOST in flags:
            scope = "host"
        else:
            scope = "global"
            gateway = Prefix(gateway)
            if dst.family == AF_UNSPEC:
                dst.family = gateway.family

        # protocol
        if _RTF_STATIC in flags:
            protocol = "static"
        elif any(flag in flags for flag in (_RTF_DYNAMIC, _RTF_MODIFIED)):
            protocol = "redirect"
        else:
            protocol = "kernel"

        self._route = {
            "type": addr_type,
            "dst": dst,
            "gateway": gateway,
            "dev": dev,
            "protocol": protocol,
            "scope": scope,
            "expire": int(expire) if expire and expire.isdigit() else None,
            "prefsrc": Prefix(src) if src else None,
            "flags": [],
        }

    def __getitem__(self, key):
        return self._route.get(key)

    def __setitem__(self, key, value):
        self._route[key] = value

    def __delitem__(self, key):
        if self._present(self._route, key):
            del self._route[key]

    def __contains__(self, other):
        return other in self._route

    @staticmethod
    def _present(data, key, value=None):
        if value is None:
            return key in data and data[key] is not None
        return data.get[key] == value

    def present(self, key, value=None):
        return self._present(self._route, key, value=value)

    def get(self, key, value=None):
        return self._route.get(key, value)

    def pop(self, key, value=None):
        if value is None:
            return self._route.pop(key)
        return self._route.pop(key, value)

    def dict(self, details=True):
        """
        JSON iproute2 output represented by a dictionary
        """
        res = {}
        for key, value in self._route.items():
            if value is None:
                continue
            if not details:
                if key in _NETSTAT_DETAIL_FIELDS:
                    continue
                if key == "type" and value == "unicast":
                    continue
                if key == "scope" and value == "global":
                    continue
            res.update({key: value})
        return res

    def str(self, details=True):
        """
        Standard iproute2 output
        """
        route = self.dict(details=details)
        res = ""
        if "type" in route:
            res += route["type"] + " "
        res += str(route["dst"])
        if "gateway" in route:
            res += f" via {repr(route['gateway'])}"
        if "dev" in route:
            res += f" dev {route['dev']}"
        if "protocol" in route:
            res += f" proto {route['protocol']}"
        if "scope" in route:
            res += f" scope {route['scope']}"
        if "prefsrc" in route:
            res += f" src {repr(route['prefsrc'])}"
        return res + "\n"


class Routes:
    __slots__ = "_routes"

    _route = re.compile(
        rf"^(?P<dst>(?:default|{IPV4ADDR}|{IPV6ADDR}))(?:%\w+)?(?:/(?P<prefix>\d+))?"
        rf"\s+(?P<gateway>{IPV4ADDR}|{IPV6ADDR}|{LLADDR}|{IFNAME}|link#\d+)(?:%\w+)?"
        r"\s+(?P<flags>\w+)"
        r"\s+(?P<dev>\w+)"
        r"\s+(?P<expire>\S+)?$",
        flags=re.MULTILINE,
    )

    def __init__(self):
        res = shell(_NETSTAT, "-n", "-r")
        links = ifconfig.Ifconfig()
        self._routes = []
        for route in self._route.finditer(res):
            dst, prefix, gateway, flags, dev, expire = route.groups()
            if _RTF_WASCLONED in flags:
                debug(f"Skip cloned rotue: {route.group()}")
                continue
            if _RTF_PROXY in flags:
                debug(f"Skip proxy rotue: {route.group()}")
                continue
            if dst == gateway:
                debug(f"Skip self rotue: {route.group()}")
                continue
            dst = Prefix(f"{dst}/{prefix}", pack=True) if prefix is not None else Prefix(dst)
            if not dst.is_default and not dst.is_host:
                addr_info = next((l["addr_info"] for l in links if l.ifname == dev and l.present("addr_info")), [])
                src = next((a["local"] for a in addr_info if a.get("local") in dst), None)
            else:
                src = None
            self._routes.append(_Route(dst, prefix, gateway, flags, dev, expire, src))

    def __len__(self):
        return len(self._routes)

    def __getitem__(self, index):
        return self._routes[index]

    def pop(self, index=-1):
        return self._routes.pop(index)

    def set(self, routes):
        if not isinstance(routes, list) or not all(isinstance(r, _Route) for r in routes):
            raise ValueError("argument is not list() of <class 'netstat._Route'>")
        self._routes = routes

    def dict(self, details=True):
        """
        List route dictiornaries
        """
        return [r.dict(details=details) for r in self._routes if details or not re.match(LLADDR, str(r["gateway"]))]

    def str(self, details=True):
        res = ""
        for r in self._routes:
            res += r.str(details=details)
        return res


class _RouteGet:
    __slots__ = "_route"

    _route_get = re.compile(
        rf"\s+route to: (?P<to>default|{IPV4ADDR}|{IPV6ADDR})\n"
        rf"destination: (?P<dst>default|{IPV4ADDR}|{IPV6ADDR})\n"
        rf"(?:\s+mask: (?P<mask>default|{IPV4ADDR}|{IPV6ADDR})\n)?"
        rf"(?:\s+gateway: (?P<gateway>default|{IPV4ADDR}|{IPV6ADDR})\n)?"
        rf"\s+interface: (?P<dev>{IFNAME})\n"
        r"\s+flags: <(?P<flags>.*)>\n"
        r"\s+recvpipe\s+sendpipe\s+ssthresh\s+rtt,msec\s+rttvar\s+hopcount\s+mtu\s+expire\n"
        r"\s+(?P<recvpipe>\d+)"
        r"\s+(?P<sendpipe>\d+)"
        r"\s+(?P<ssthresh>\d+)"
        r"\s+(?P<rtt>\d+)"
        r"\s+(?P<rttvar>\d+)"
        r"\s+(?P<hopcount>\d+)"
        r"\s+(?P<mtu>\d+)"
        r"\s+(?P<expire>\d+)"
    )

    def __init__(self, data, uid=None):
        self._route = {}
        route = self._route_get.search(data)
        if not route:
            return
        to, dst, mask, gateway, dev, flags, recvpipe, sendpipe, ssthresh, rtt, rttvar, hopcount, mtu, expire = route.groups()
        # recvpipe = int(recvpipe)
        # sendpipe = int(sendpipe)
        # ssthresh = int(ssthresh)
        # rtt = int(rtt)
        # rttvar = int(rttvar)
        # hopcount = int(hopcount)
        mtu = int(mtu)
        expire = int(expire)
        self._route["dst"] = Prefix(to, pack=True)
        if gateway:
            self._route["gateway"] = Prefix(gateway)
        self._route["dev"] = dev
        try:
            self._route["prefsrc"] = get_prefsrc(self._route["dst"])
        except Exception:
            pass
        self._route["flags"] = flags.split(",") if flags != "" else []
        if uid is not None:
            self._route["uid"] = uid
        self._route["metrics"] = [{"mtu": mtu}]
        self._route["cache"] = []
        if expire:
            route["cache"].append({"expire": expire})

    def dict(self, details=True):
        """
        JSON iproute2 output represented by a dictionary
        """
        res = {}
        for key, value in self._route.items():
            if value is None:
                continue
            if not details:
                if key in _ROUTE_GET_DETAIL_FIELDS:
                    continue
                if key == "type" and value == "unicast":
                    continue
            res.update({key: value})
        return res

    def str(self, details=True):
        """
        Standard iproute2 output
        """
        if not (route := self.dict(details=details)):
            return ""

        res = ""
        if "type" in route:
            res += route["type"] + " "
        res += str(route["dst"])
        if "gateway" in route:
            res += " via " + repr(route["gateway"])
        if "dev" in route:
            res += " dev " + route["dev"]
        if "prefsrc" in route:
            res += " src " + route["prefsrc"]
        if "uid" in route:
            res += " uid " + str(route["uid"])
        res += "\n"

        res += "    cache"
        for key, value in route["cache"]:
            res += f" {key} {value}"
        res += "\n"

        return res


class RouteGet:
    __slots__ = "_route"

    def __init__(self, host, uid=None):
        res = shell(_ROUTE, "-n", "get", "-inet" if host.version == 4 else "-inet6", repr(host))
        self._route = _RouteGet(res, uid=uid)

    def dict(self, details=True):
        return [self._route.dict(details=details)] if self._route._route else []

    def str(self, details=True):
        return self._route.str(details=details)
