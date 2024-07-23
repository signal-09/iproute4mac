import iproute4mac.netstat as netstat
import iproute4mac.route as route

from iproute4mac.utils import *


def usage():
    stderr("""\
Usage: ip route { list | flush } SELECTOR
       ip route save SELECTOR
       ip route restore
       ip route showdump
       ip route get [ ROUTE_GET_FLAGS ] [ to ] ADDRESS
                            [ from ADDRESS iif STRING ]
                            [ oif STRING ] [ tos TOS ]
                            [ mark NUMBER ] [ vrf NAME ]
                            [ uid NUMBER ] [ ipproto PROTOCOL ]
                            [ sport NUMBER ] [ dport NUMBER ]
                            [ as ADDRESS ]
       ip route { add | del | change | append | replace } ROUTE
SELECTOR := [ root PREFIX ] [ match PREFIX ] [ exact PREFIX ]
            [ table TABLE_ID ] [ vrf NAME ] [ proto RTPROTO ]
            [ type TYPE ] [ scope SCOPE ]
ROUTE := NODE_SPEC [ INFO_SPEC ]
NODE_SPEC := [ TYPE ] PREFIX [ tos TOS ]
             [ table TABLE_ID ] [ proto RTPROTO ]
             [ scope SCOPE ] [ metric METRIC ]
             [ ttl-propagate { enabled | disabled } ]
INFO_SPEC := { NH | nhid ID } OPTIONS FLAGS [ nexthop NH ]...
NH := [ encap ENCAPTYPE ENCAPHDR ] [ via [ FAMILY ] ADDRESS ]
      [ dev STRING ] [ weight NUMBER ] NHFLAGS
FAMILY := [ inet | inet6 | mpls | bridge | link ]
OPTIONS := FLAGS [ mtu NUMBER ] [ advmss NUMBER ] [ as [ to ] ADDRESS ]
           [ rtt TIME ] [ rttvar TIME ] [ reordering NUMBER ]
           [ window NUMBER ] [ cwnd NUMBER ] [ initcwnd NUMBER ]
           [ ssthresh NUMBER ] [ realms REALM ] [ src ADDRESS ]
           [ rto_min TIME ] [ hoplimit NUMBER ] [ initrwnd NUMBER ]
           [ features FEATURES ] [ quickack BOOL ] [ congctl NAME ]
           [ pref PREF ] [ expires TIME ] [ fastopen_no_cookie BOOL ]
TYPE := { unicast | local | broadcast | multicast | throw |
          unreachable | prohibit | blackhole | nat }
TABLE_ID := [ local | main | default | all | NUMBER ]
SCOPE := [ host | link | global | NUMBER ]
NHFLAGS := [ onlink | pervasive ]
RTPROTO := [ kernel | boot | static | NUMBER ]
PREF := [ low | medium | high ]
TIME := NUMBER[s|ms]
BOOL := [1|0]
FEATURES := ecn
ENCAPTYPE := [ mpls | ip | ip6 | seg6 | seg6local | rpl | ioam6 | xfrm ]
ENCAPHDR := [ MPLSLABEL | SEG6HDR | SEG6LOCAL | IOAM6HDR | XFRMINFO ]
SEG6HDR := [ mode SEGMODE ] segs ADDR1,ADDRi,ADDRn [hmac HMACKEYID] [cleanup]
SEGMODE := [ encap | encap.red | inline | l2encap | l2encap.red ]
SEG6LOCAL := action ACTION [ OPTIONS ] [ count ]
ACTION := { End | End.X | End.T | End.DX2 | End.DX6 | End.DX4 |
            End.DT6 | End.DT4 | End.DT46 | End.B6 | End.B6.Encaps |
            End.BM | End.S | End.AS | End.AM | End.BPF }
OPTIONS := OPTION [ OPTIONS ]
OPTION := { flavors FLAVORS | srh SEG6HDR | nh4 ADDR | nh6 ADDR | iif DEV | oif DEV |
            table TABLEID | vrftable TABLEID | endpoint PROGNAME }
            table TABLEID | vrftable TABLEID | endpoint PROGNAME }
FLAVORS := { FLAVOR[,FLAVOR] }
FLAVOR := { psp | usp | usd | next-csid }
IOAM6HDR := trace prealloc type IOAM6_TRACE_TYPE ns IOAM6_NAMESPACE size IOAM6_TRACE_SIZE
XFRMINFO := if_id IF_ID [ link_dev LINK ]
ROUTE_GET_FLAGS := ROUTE_GET_FLAG [ ROUTE_GET_FLAGS ]
ROUTE_GET_FLAG := [ connected | fibmatch | notify ]""")
    exit(-1)


def iproute_modify(argv, option):
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "src"):
            src = next_arg(argv)
            do_notimplemented([src])
        elif strcmp(opt, "as"):
            addr = next_arg(argv)
            if strcmp(addr, "to"):
                addr = next_arg(argv)
            do_notimplemented([addr])

    return EXIT_SUCCESS


def iproute_get(argv, option):
    prefix = None

    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "tos") or matches(opt, "dsfield"):
            tos = next_arg(argv)
            do_notimplemented([tos])
        elif matches(opt, "from"):
            addr = next_arg(argv)
            if matches(addr, "help"):
                usage()
            do_notimplemented([addr])
        elif matches(opt, "iif"):
            idev = next_arg(argv)
            do_notimplemented([idev])
        elif matches(opt, "mark"):
            mark = next_arg(argv)
            do_notimplemented([mark])
        elif matches(opt, "oif"):
            odev = next_arg(argv)
            do_notimplemented([odev])
        elif matches(opt, "oif"):
            odev = next_arg(argv)
            do_notimplemented([odev])
        elif matches(opt, "notify"):
            do_notimplemented()
        elif matches(opt, "connected"):
            do_notimplemented()
        elif matches(opt, "vrf"):
            odev = next_arg(argv)
            do_notimplemented([odev])
        elif matches(opt, "uid"):
            uid = next_arg(argv)
            try:
                uid = int(uid)
                assert 0 <= uid < 2**32
            except (ValueError, AssertionError):
                invarg("invalid UID", uid)
            option["uid"] = uid
        elif matches(opt, "fibmatch"):
            do_notimplemented()
        elif strcmp(opt, "as"):
            addr = next_arg(argv)
            if strcmp(addr, "to"):
                addr = next_arg(argv)
            addr = get_addr(addr, option["preferred_family"])
            do_notimplemented()
        elif matches(opt, "sport"):
            sport = next_arg(argv)
            try:
                sport = int(sport)
            except ValueError:
                invarg("invalid sport", sport)
            do_notimplemented([sport])
        elif matches(opt, "dport"):
            dport = next_arg(argv)
            try:
                dport = int(dport)
            except ValueError:
                invarg("invalid dport", dport)
            do_notimplemented([dport])
        elif matches(opt, "ipproto"):
            ipproto = next_arg(argv)
            try:
                ipproto = int(ipproto)
            except ValueError:
                invarg('Invalid "ipproto" value', ipproto)
            do_notimplemented([ipproto])
        else:
            if strcmp(opt, "to"):
                opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            prefix = get_prefix(opt, option["preferred_family"])
            if not prefix.is_host:
                stderr(
                    f"Warning: /{prefix.prefixlen} as prefix is invalid, only /{prefix._max_prefixlen} (or none) is supported."
                )
                prefix = Prefix(str(prefix.address))

    if not prefix:
        stderr("need at least a destination address")
        return EXIT_FAILURE

    args = ["-n", "get"]
    if prefix.version == 6 or option["preferred_family"] == AF_INET6:
        args += ["-inet6"]

    stdout = route.exec(args + [str(prefix)])
    get = route.parse(stdout, option)
    route.dumps(get, option)
    return EXIT_SUCCESS


# ip route [ list [ SELECTOR ] ]
# SELECTOR := [ root PREFIX ] [ match PREFIX ] [ exact PREFIX ]
#             [ table TABLE_ID ] [ vrf NAME ] [ proto RTPROTO ]
#             [ type TYPE ] [ scope SCOPE ]
# TYPE := { unicast | local | broadcast | multicast | throw |
#           unreachable | prohibit | blackhole | nat }
# TABLE_ID := [ local | main | default | all | NUMBER ]
# SCOPE := [ host | link | global | NUMBER ]
# RTPROTO := [ kernel | boot | static | NUMBER ]
def iproute_list(argv, option):
    if option["preferred_family"] == AF_UNSPEC:
        option["preferred_family"] = AF_INET

    stdout = netstat.exec(["-n", "-r"])
    routes = netstat.parse(stdout, option)
    while argv:
        opt = argv.pop(0)
        if matches(opt, "table"):
            table = next_arg(argv)
            do_notimplemented([table])
        elif matches(opt, "vrf"):
            tid = next_arg(argv)
            do_notimplemented([tid])
        elif matches(opt, "cached", "cloned"):
            do_notimplemented()
        elif strcmp(opt, "tod") or matches(opt, "dsfield"):
            tos = next_arg(argv)
            do_notimplemented([tos])
        elif matches(opt, "protocol"):
            protocol = next_arg(argv)
            if protocol not in ("static", "redirect", "kernel", "all"):
                invarg('invalid "protocol"', protocol)
            if protocol == "all":
                continue
            routes = [route for route in routes if "protocol" in route and route["protocol"] == protocol]
        elif matches(opt, "scope"):
            scope = next_arg(argv)
            if scope not in ("link", "host", "global", "all") and not scope.isdigit():
                invarg('invalid "scope"', scope)
            if scope == "all":
                continue
            # FIXME: numeric scope?
            routes = [route for route in routes if "scope" in route and route["scope"] == scope]
            delete_keys(routes, "scope")
        elif matches(opt, "type"):
            addr_type = next_arg(argv)
            if addr_type not in ("blackhole", "broadcast", "multicast", "unicast"):
                invarg("node type value is invalid", addr_type)
            routes = [
                route
                for route in routes
                if (("type" in route and route["type"] == addr_type) or ("type" not in route and addr_type == "unicast"))
            ]
        elif strcmp(opt, "dev", "oif", "iif"):
            dev = next_arg(argv)
            routes = [route for route in routes if "dev" in route and route["dev"] == dev]
            delete_keys(routes, "dev")
        elif strcmp(opt, "mark"):
            mark = next_arg(argv)
            do_notimplemented([mark])
        elif matches(opt, "metric", "priority") or strcmp(opt, "preference"):
            metric = next_arg(argv)
            try:
                metric = int(metric)
            except ValueError:
                invarg('"metric" value is invalid', metric)
            do_notimplemented()
        elif strcmp(opt, "via"):
            via = next_arg(argv)
            family = read_family(via)
            if family == AF_UNSPEC:
                family = option["preferred_family"]
            else:
                via = next_arg(argv)
            prefix = get_prefix(via, family)
            routes = [route for route in routes if "gateway" in route and prefix in Prefix(route["gateway"])]
            delete_keys(routes, "gateway")
        elif strcmp(opt, "src"):
            src = next_arg(argv)
            do_notimplemented([src])
        elif matches(opt, "realms"):
            realm = next_arg(argv)
            do_notimplemented([realm])
        elif matches(opt, "from"):
            opt = next_arg(argv)
            if matches(opt, "root"):
                opt = next_arg(argv)
                prefix = get_prefix(opt, option["preferred_family"])
                do_notimplemented()
            elif matches(opt, "match"):
                opt = next_arg(argv)
                prefix = get_prefix(opt, option["preferred_family"])
                do_notimplemented()
            else:
                if matches(opt, "exact"):
                    opt = next_arg(argv)
                prefix = get_prefix(opt, option["preferred_family"])
                do_notimplemented()
        else:
            if matches(opt, "to"):
                opt = next_arg(argv)
            if matches(opt, "root"):
                opt = next_arg(argv)
                prefix = get_prefix(opt, option["preferred_family"])
                do_notimplemented()
            elif matches(opt, "match"):
                opt = next_arg(argv)
                prefix = get_prefix(opt, option["preferred_family"])
                routes = [route for route in routes if "dst" in route and prefix in Prefix(route["dst"])]
            else:
                if matches(opt, "exact"):
                    opt = next_arg(argv)
                prefix = get_prefix(opt, option["preferred_family"])
                routes = [route for route in routes if "dst" in route and prefix == Prefix(route["dst"])]

    netstat.dumps(routes, option)
    return EXIT_SUCCESS


def do_iproute(argv, option):
    if not argv:
        return iproute_list(argv, option)

    cmd = argv.pop(0)
    if "add".startswith(cmd):
        return iproute_modify(argv, option)
    elif "change".startswith(cmd):
        return do_notimplemented()
    elif "replace".startswith(cmd):
        return do_notimplemented()
    elif "prepend".startswith(cmd):
        return do_notimplemented()
    elif "append".startswith(cmd):
        return do_notimplemented()
    elif "test".startswith(cmd):
        return do_notimplemented()
    elif "delete".startswith(cmd):
        return do_notimplemented()
    elif "show".startswith(cmd) or "lst".startswith(cmd) or "list".startswith(cmd):
        return iproute_list(argv, option)
    elif "get".startswith(cmd):
        return iproute_get(argv, option)
    elif "flush".startswith(cmd):
        return do_notimplemented()
    elif "save".startswith(cmd):
        return do_notimplemented()
    elif "restore".startswith(cmd):
        return do_notimplemented()
    elif "showdump".startswith(cmd):
        return do_notimplemented()
    elif "help".startswith(cmd):
        return usage()

    stderr(f'Command "{cmd}" is unknown, try "ip route help".')
    exit(-1)
