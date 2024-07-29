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
            route = match.route.groupdict()
            debug(f"Found route {route}")

            if route["flags"] == RTF_WASCLONED or route["flags"] == RTF_PROXY:
                debug("Skip cloned/proxy rotue")
                continue

            if re.search(LLADDR, route["gateway"]):
                if not OPTION["show_details"]:
                    debug("Skip host rotue")
                    continue
                del route["gateway"]

            if re.match(IPV4ADDR, route["dst"]) or ("gateway" in route and re.match(IPV4ADDR, route["gateway"])):
                family = AF_INET
            else:
                family = AF_INET6
            if family == AF_INET and OPTION["preferred_family"] == AF_INET6:
                debug("Skip IPv4 rotue")
                continue
            if family == AF_INET6 and OPTION["preferred_family"] == AF_INET:
                debug("Skip IPv6 rotue")
                continue

            if route["dst"] != "default" and family == AF_INET:
                dots = route["dst"].count(".")
                if dots < 3:
                    route["dst"] = route["dst"] + ".0" * (3 - dots)
                    if not route["prefix"]:
                        route["prefix"] = 8 * (dots + 1)
            if route["prefix"]:
                route["dst"] = f"{route["dst"]}/{route["prefix"]}"

            # protocol
            if RTF_STATIC in route["flags"]:
                protocol = "static"
            elif any(flag in route["flags"] for flag in (RTF_DYNAMIC, RTF_MODIFIED)):
                protocol = "redirect"
            else:
                protocol = "kernel"

            # scope
            if RTF_HOST in route["flags"]:
                scope = "host"
            if "gateway" in route and route["gateway"].startswith("link#"):
                scope = "link"
                del route["gateway"]
            elif OPTION["show_details"]:
                scope = "global"
            else:
                scope = None

            # address type
            if RTF_BLACKHOLE in route["flags"]:
                addr_type = "blackhole"
            elif RTF_BROADCAST in route["flags"]:
                addr_type = "broadcast"
            elif RTF_MULTICAST in route["flags"]:
                addr_type = "multicast"
            elif OPTION["show_details"]:
                addr_type = "unicast"
            else:
                addr_type = None

            route = {
                "type": addr_type,
                "dst": route["dst"],
                "gateway": route["gateway"] if "gateway" in route else None,
                "dev": route["dev"],
                "protocol": protocol,
                "scope": scope,
                "expire": int(route["expire"]) if route["expire"] and route["expire"] != "!" else None,
                "flags": [],
            }
            routes.append({k: v for k, v in route.items() if v is not None})
        elif line:
            debug(f'Unparsed line "{line.strip()}"')

    return routes
