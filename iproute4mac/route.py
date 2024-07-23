import re

from iproute4mac.utils import *


def exec(args=[]):
    return shell(["route"] + args)


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
