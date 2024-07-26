import re

from iproute4mac.utils import *


ROUTE_DUMP_MAGIC = 0x45311224

RTN_UNSPEC = 0
RTN_UNICAST = 1
RTN_LOCAL = 2
RTN_BROADCAST = 3
RTN_ANYCAST = 4
RTN_MULTICAST = 5
RTN_BLACKHOLE = 6
RTN_UNREACHABLE = 7
RTN_PROHIBIT = 8
RTN_THROW = 9
RTN_NAT = 10
RTN_XRESOLVE = 11
__RTN_MAX = 12

RTN_MAP = (
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


def get_rtn(name):
    if name.isdigit():
        rtn = int(name)
    else:
        rtn = RTN_MAP.index(name)
    if not 0 < rtn < 2**8:
        raise ValueError
    return rtn


def is_rtn(name):
    try:
        get_rtn(name)
    except ValueError:
        return False
    return True


def exec(*argv):
    return shell("route", *argv)


def dumps(routes, option):
    if option["json"]:
        print(json_dumps(routes, option["pretty"]))
        return

    if not routes:
        return

    for route in routes:
        stdout(route["dst"])
        if "gateway" in route:
            stdout(f" via {route['gateway']}")
        if "dev" in route:
            stdout(f" dev {route['dev']}")
        if "prefsrc" in route:
            stdout(f" src {route['prefsrc']}")
        if "uid" in route:
            stdout(f" uid {route['uid']}")
        stdout(end="\n")


class routeGetRegEx:
    _dst = re.compile(rf"\s+route to: (?P<dst>{IPV4ADDR}|{IPV6ADDR})")
    _gateway = re.compile(rf"\s+gateway: (?P<gateway>default|{IPV4ADDR}|{IPV6ADDR})")
    _dev = re.compile(r"\s+interface: (?P<dev>\w+)")
    _flags = re.compile(r"\s+flags: <(?P<flags>.*)>")
    _data = re.compile(
        r"\s+(?P<recvpipe>\d+)"
        r"\s+(?P<sendpipe>\d+)"
        r"\s+(?P<ssthresh>\d+)"
        r"\s+(?P<rtt>\d+)"
        r"\s+(?P<rttvar>\d+)"
        r"\s+(?P<hopcount>\d+)"
        r"\s+(?P<mtu>\d+)"
        r"\s+(?P<expire>\d+)"
    )

    def __init__(self, line):
        self.dst = self._dst.match(line)
        self.gateway = self._gateway.match(line)
        self.dev = self._dev.match(line)
        self.flags = self._flags.match(line)
        self.data = self._data.match(line)


def parse(res, option):
    route = {}
    for line in iter(res.split("\n")):
        match = routeGetRegEx(line)

        if match.dst:
            route["dst"] = match.dst.group("dst")
        elif match.gateway:
            route["gateway"] = match.gateway.group("gateway")
        elif match.dev:
            route["dev"] = match.dev.group("dev")
        elif match.flags:
            try:
                route["prefsrc"] = get_prefsrc(route["dst"], option["preferred_family"])
            except Exception:
                pass
            route["flags"] = match.flags.group("flags")
            route["flags"] = route["flags"].split(",") if route["flags"] != "" else []
            route["uid"] = option["uid"]
        elif match.data:
            data = match.data.groupdict()
            for key in data:
                data[key] = int(data[key])
            route["metrics"] = [{"mtu": data["mtu"]}]
            route["cache"] = []
            if data["expire"]:
                route["cache"].append({"expire": data["expire"]})

    return [route] if route else []
