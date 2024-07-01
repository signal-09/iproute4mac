import iproute4mac.netstat as netstat
from iproute4mac.utils import *


''' Options '''
option = {}


def do_iproute_usage():
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
def do_iproute_list(argv=[]):
    routes = netstat.routes(argv, option)
    #delete_keys(links, ['addr_info'])
    netstat.dumps(routes, option)
    return EXIT_SUCCESS


def do_iproute(argv=[], opts={}):
    global option
    option = opts

    if not argv:
        return do_iproute_list()

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
        return do_iproute_list(argv)
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
        return do_iproute_usage()

    stderr('Command "%s" is unknown, try "ip route help".' % cmd)
    exit(-1)
