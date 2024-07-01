import subprocess
import iproute4mac.netstat as netstat

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
    cmd = subprocess.run(['netstat', '-n', '-r'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         encoding="utf-8")
    if cmd.returncode != 0:
        print(cmd.stderr)
        exit(cmd.returncode)

    if option['preferred_family'] == AF_UNSPEC:
        option['preferred_family'] = AF_INET

    routes = netstat.parse(cmd.stdout, option)
    while argv:
        opt = argv.pop(0)
        if opt == 'table':
            # table = next_arg(argv)
            do_notimplemented()
        elif opt == 'vrf':
            # tid = next_arg(argv)
            do_notimplemented()
        elif opt in ('cached', 'cloned'):
            do_notimplemented()
        elif opt in ('tod', 'dsfield'):
            # tos = next_arg(argv)
            do_notimplemented()
        elif opt == 'protocol':
            protocol = next_arg(argv)
            if protocol not in ('static', 'redirect', 'kernel', 'all'):
                invarg('invalid "protocol"', protocol)
            if protocol == 'all':
                continue
            routes = [route for route in routes if 'protocol' in route and route['protocol'] == protocol]
        elif opt == 'scope':
            scope = next_arg(argv)
            if (scope not in ('link', 'host', 'global', 'all')
               and not scope.isnumeric()):
                invarg('invalid "scope"', scope)
            if scope == 'all':
                continue
            # FIXME: numeric scope?
            routes = [route for route in routes if 'scope' in route and route['scope'] == scope]
        elif opt == 'type':
            addr_type = next_arg(argv)
            if addr_type not in ('blackhole', 'broadcast', 'multicast', 'unicast'):
                invarg('node type value is invalid', addr_type)
            routes = [route for route in routes if (('type' in route and route['type'] == addr_type)
                                                    or ('type' not in route and addr_type == 'unicast'))]
        elif opt in ('dev', 'oif', 'iif'):
            dev = next_arg(argv)
            routes = [route for route in routes if 'dev' in route and route['dev'] == dev]
        elif opt == 'mark':
            # tid = next_arg(argv)
            do_notimplemented()
        elif opt in ('metric', 'priority', 'preference'):
            metric = next_arg(argv)
            try:
                metric = int(metric)
            except ValueError:
                invarg('"metric" value is invalid', metric)
            do_notimplemented()
        elif opt == 'via':
            via = next_arg(argv)
            family = read_family(via)
            if family == AF_UNSPEC:
                family = option['preferred_family']
            else:
                via = next_arg(argv)
            do_notimplemented()
        elif opt == 'src':
            # src = next_arg(argv)
            do_notimplemented()
        elif opt == 'from':
            opt = next_arg(argv)
            if opt == 'root':
                opt = next_arg(argv)
                # get_prefix(opt, option['preferred_family'])
            elif opt == 'match':
                opt = next_arg(argv)
                # get_prefix(opt, option['preferred_family'])
            else:
                if opt == 'exact':
                    opt = next_arg(argv)
                # get_prefix(opt, option['preferred_family'])
        else:
            if opt == 'to':
                opt = next_arg(argv)
            if opt == 'root':
                opt = next_arg(argv)
                # get_prefix(opt, option['preferred_family'])
            elif opt == 'match':
                opt = next_arg(argv)
                # get_prefix(opt, option['preferred_family'])
            else:
                if opt == 'exact':
                    opt = next_arg(argv)
                # get_prefix(opt, option['preferred_family'])
            do_notimplemented()

    netstat.dumps(routes, option)
    return EXIT_SUCCESS


def do_iproute(argv, option):
    if not argv:
        return iproute_list(argv, option)

    cmd = argv.pop(0)
    if 'add'.startswith(cmd):
        return do_notimplemented()
    elif 'change'.startswith(cmd):
        return do_notimplemented()
    elif 'replace'.startswith(cmd):
        return do_notimplemented()
    elif 'prepend'.startswith(cmd):
        return do_notimplemented()
    elif 'append'.startswith(cmd):
        return do_notimplemented()
    elif 'test'.startswith(cmd):
        return do_notimplemented()
    elif 'delete'.startswith(cmd):
        return do_notimplemented()
    elif ('show'.startswith(cmd)
          or 'lst'.startswith(cmd)
          or 'list'.startswith(cmd)):
        return iproute_list(argv, option)
    elif 'get'.startswith(cmd):
        return do_notimplemented()
    elif 'flush'.startswith(cmd):
        return do_notimplemented()
    elif 'save'.startswith(cmd):
        return do_notimplemented()
    elif 'restore'.startswith(cmd):
        return do_notimplemented()
    elif 'showdump'.startswith(cmd):
        return do_notimplemented()
    elif 'help'.startswith(cmd):
        return usage()

    stderr('Command "%s" is unknown, try "ip route help".' % cmd)
    exit(-1)
