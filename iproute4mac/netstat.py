import re

from iproute4mac.utils import *


"""
https://docs.freebsd.org/en/books/handbook/advanced-networking/#routeflags
"""
RTF_PROTO1 = "1"  # Protocol specific routing flag #1
RTF_PROTO2 = "2"  # Protocol specific routing flag #2
RTF_PROTO3 = "3"  # Protocol specific routing flag #3
RTF_BLACKHOLE = "B"  # Just discard packets (during updates)
RTF_BROADCAST = "b"  # The route represents a broadcast address
RTF_CLONING = "C"  # Generate new routes on use
RTF_PRCLONING = "c"  # Protocol-specified generate new routes on use
RTF_DYNAMIC = "D"  # Created dynamically (by redirect)
RTF_GATEWAY = "G"  # Destination requires forwarding by intermediary
RTF_HOST = "H"  # Host entry (net otherwise)
RTF_IFSCOPE = "I"  # Route is associated with an interface scope
RTF_IFREF = "i"  # Route is holding a reference to the interface
RTF_LLINFO = "L"  # Valid protocol to link address translation
RTF_MODIFIED = "M"  # Modified dynamically (by redirect)
RTF_MULTICAST = "m"  # The route represents a multicast address
RTF_REJECT = "R"  # Host or net unreachable
RTF_ROUTER = "r"  # Host is a default router
RTF_STATIC = "S"  # Manually added
RTF_UP = "U"  # Route usable
RTF_WASCLONED = "W"  # Route was generated as a result of cloning
RTF_XRESOLVE = "X"  # External daemon translates proto to link address
RTF_PROXY = "Y"  # Proxying; cloned routes will not be scoped
RTF_GLOBAL = "g"  # Route to a destination of the global internet (policy hint)


def exec(*argv):
    return shell("netstat", *argv)


def dumps(routes):
    if OPTION["json"]:
        print(json_dumps(routes, OPTION["pretty"]))
        return

    if not routes:
        return

    for route in routes:
        if OPTION["show_details"] or "type" in route:
            stdout(route["type"] if "type" in route else "unicast", " ")
        stdout(route["dst"])
        if "gateway" in route:
            stdout(f" via {route['gateway']}")
        if "dev" in route:
            stdout(f" dev {route['dev']}")
        if "protocol" in route:
            stdout(f" proto {route['protocol']}")
        if "scope" in route:
            stdout(f" scope {route['scope']}")
        if "prefsrc" in route:
            stdout(f" src {route['src']}")
        stdout(end="\n")


class netstatRegEx:
    _route = re.compile(
        rf"(?P<dst>(?:default|{IPV4ADDR}|{IPV6ADDR}))(?:%\w+)?(?:/(?P<prefix>\d+))?"
        rf"\s+(?P<gateway>{IPV4ADDR}|{IPV6ADDR}|{LLADDR}|link#\d+)(?:%\w+)?"
        r"\s+(?P<flags>\w+)"
        r"\s+(?P<dev>\w+)"
        r"\s+(?P<expire>\S+)?"
    )

    def __init__(self, line):
        self.route = self._route.match(line)


def parse(res):
    routes = []
    for line in iter(res.split("\n")):
        match = netstatRegEx(line)

        if match.route:
            debug(f"Found route: {line.strip()}")
            dst, prefix, gateway, flags, dev, expire = match.route.groups()

            if RTF_WASCLONED in flags:
                debug("Skip cloned rotue")
                continue
            if RTF_PROXY in flags:
                debug("Skip proxy rotue")
                continue

            if prefix:
                dst = f"{dst}/{prefix}"
            dst = Prefix(dst)

            scope = None
            if re.match(LLADDR, gateway):
                if not OPTION["show_details"]:
                    debug("Skip host rotue")
                    continue
                gateway = None
            elif gateway.startswith("link#"):
                scope = "link"
                gateway = None
            else:
                gateway = Prefix(gateway)
                if dst.family == AF_UNSPEC:
                    dst.family = gateway.family

            if OPTION["preferred_family"] != AF_UNSPEC and dst.family != OPTION["preferred_family"]:
                debug("Skip unmatched IP version rotue")
                continue

            # protocol
            if RTF_STATIC in flags:
                protocol = "static"
            elif any(flag in flags for flag in (RTF_DYNAMIC, RTF_MODIFIED)):
                protocol = "redirect"
            else:
                protocol = "kernel"

            # scope
            if RTF_HOST in flags:
                scope = "host"
            elif OPTION["show_details"]:
                scope = "global"

            # address type
            if RTF_BLACKHOLE in flags:
                addr_type = "blackhole"
            elif RTF_BROADCAST in flags:
                addr_type = "broadcast"
            elif RTF_MULTICAST in flags:
                addr_type = "multicast"
            elif OPTION["show_details"]:
                addr_type = "unicast"
            else:
                addr_type = None

            route = {
                "type": addr_type,
                "dst": dst,
                "gateway": gateway,
                "dev": dev,
                "protocol": protocol,
                "scope": scope,
                "expire": int(expire) if expire and expire.isdigit() else None,
                "flags": [],
            }
            routes.append({k: v for k, v in route.items() if v is not None})
        elif line:
            debug(f'Unparsed line "{line.strip()}"')

    return routes
