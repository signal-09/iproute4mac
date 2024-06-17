#!/usr/bin/env python3

import os
import sys

from iproute4mac.utils import *
from iproute4mac.iplink import *
from iproute4mac.ipaddress import *


''' Costants '''
VERSION = '0.1.0'


def do_help(argv=[], option={}):
    usage()

def usage():
    stderr("""\
Usage: ip [ OPTIONS ] OBJECT { COMMAND | help }
       ip [ -force ] -batch filename
where  OBJECT := { address | addrlabel | fou | help | ila | ioam | l2tp | link |
                   macsec | maddress | monitor | mptcp | mroute | mrule |
                   neighbor | neighbour | netconf | netns | nexthop | ntable |
                   ntbl | route | rule | sr | stats | tap | tcpmetrics |
                   token | tunnel | tuntap | vrf | xfrm }
       OPTIONS := { -V[ersion] | -s[tatistics] | -d[etails] | -r[esolve] |
                    -h[uman-readable] | -iec | -j[son] | -p[retty] |
                    -f[amily] { inet | inet6 | mpls | bridge | link } |
                    -4 | -6 | -M | -B | -0 |
                    -l[oops] { maximum-addr-flush-attempts } | -echo | -br[ief] |
                    -o[neline] | -t[imestamp] | -ts[hort] | -b[atch] [filename] |
                    -rc[vbuf] [size] | -n[etns] name | -N[umeric] | -a[ll] |
                    -c[olor]}""")
    exit(-1)


''' Implemented objects '''
objs = [
    ('address', do_ipaddr),
    ('addrlabel', do_notimplemented),
    ('maddress', do_notimplemented),
    ('route', do_notimplemented),
    ('rule', do_notimplemented),
    ('neighbor', do_notimplemented),
    ('neighbour', do_notimplemented),
    ('ntable', do_notimplemented),
    ('ntbl', do_notimplemented),
    ('link', do_iplink),
    ('l2tp', do_notimplemented),
    ('fou', do_notimplemented),
    ('ila', do_notimplemented),
    ('macsec', do_notimplemented),
    ('tunnel', do_notimplemented),
    ('tunl', do_notimplemented),
    ('tuntap', do_notimplemented),
    ('tap', do_notimplemented),
    ('token', do_notimplemented),
    ('tcpmetrics', do_notimplemented),
    ('tcp_metrics', do_notimplemented),
    ('monitor', do_notimplemented),
    ('xfrm', do_notimplemented),
    ('mroute', do_notimplemented),
    ('mrule', do_notimplemented),
    ('netns', do_notimplemented),
    ('netconf', do_notimplemented),
    ('vrf', do_notimplemented),
    ('sr', do_notimplemented),
    ('nexthop', do_notimplemented),
    ('mptcp', do_notimplemented),
    ('ioam', do_notimplemented),
    ('help', do_help),
    ('stats', do_notimplemented)
]


def do_obj(argv, option):
    obj = argv.pop(0)
    for o, f in objs:
        if o.startswith(obj):
            return f(argv, option)

    stderr('Object "%s" is unknown, try "ip help".' % obj)
    return EXIT_FAILURE


def main():
    batch_file = None
    option = {
        'preferred_family': AF_UNSPEC,
        'human_readable': False,
        'use_iec': False,
        'show_stats': False,
        'show_details': False,
        'oneline': False,
        'brief': False,
        'json': False,
        'pretty': False,
        'timestamp': False,
        'timestamp_short': False,
        'echo_request': False,
        'force': False,
        'max_flush_loops': 10,
        'batch_mode': False,
        'do_all': False
    }

    if sys.platform != 'darwin':
        stderr('Unupported OS.')
        exit(-1)

    argv = sys.argv[1:]
    while argv:
        if argv[0] == '--':
            argv.pop(0)
            break
        elif argv[0][0] != '-':
            break

        opt = argv.pop(0)
        if opt[1] == '-':
            opt = opt[1:]

        if '-loops'.startswith(opt):
            try:
                max_flush_loops = int(argv.pop(0))
            except IndexError:
                missarg('loop count')
            except ValueError:
                error('loop count not a number')
        elif '-family'.startswith(opt):
            try:
                opt = argv.pop(0)
            except IndexError:
                missarg('family type')
            if opt == 'help':
                usage()
            option['preferred_family'] = read_family(opt)
            if option['preferred_family'] == AF_UNSPEC:
                invarg('invalid protocol family', opt)
        elif opt == '-4':
            option['preferred_family'] = AF_INET
        elif opt == '-6':
            option['preferred_family'] = AF_INET6
        elif opt == '-0':
            option['preferred_family'] = AF_PACKET
        elif opt == '-M':
            option['preferred_family'] = AF_MPLS
        elif opt == '-B':
            option['preferred_family'] = AF_BRIDGE
        elif '-human-readable'.startswith(opt):
            option['human_readable'] = True
        elif '-iec'.startswith(opt):
            option['use_iec'] = True
        elif '-stats'.startswith(opt) or '-statistics'.startswith(opt):
            option['show_stats'] = True
        elif '-details'.startswith(opt):
            option['show_details'] = True
        elif '-resolve'.startswith(opt):
            option['resolve_hosts'] = True
        elif '-oneline'.startswith(opt):
            option['oneline'] = True
        elif '-timestamp'.startswith(opt):
            option['timestamp'] = True
        elif '-tshort'.startswith(opt):
            option['timestamp'] = True
            option['timestamp_short'] = True
        elif '-Version'.startswith(opt):
            print('ip wrapper, iproute4mac-%s' % VERSION)
            exit(0)
        elif '-force'.startswith(opt):
            option['force'] = True
        elif '-batch'.startswith(opt):
            try:
                batch_file = argv.pop(0)
            except IndexError:
                missarg('batch file')
        elif '-brief'.startswith(opt):
            option['brief'] = True
        elif '-json'.startswith(opt):
            option['json'] = True
        elif '-pretty'.startswith(opt):
            option['pretty'] = True
        elif '-rcvbuf'.startswith(opt):
            try:
                option['rcvbuf'] = int(argv.pop(0))
            except IndexError:
                missarg('rcvbuf size')
            except ValueError:
                error('rcvbuf size not a number')
        elif matches_color(opt):
            # Color option is not implemented
            pass
        elif '-help'.startswith(opt):
            usage()
        elif '-netns'.startswith(opt):
            do_notimplemented()
        elif '-Numeric'.startswith(opt):
            option['numeric'] = True
        elif '-all'.startswith(opt):
            option['do_all'] = True
        elif opt == '-echo':
            option['echo_request'] = True
        else:
            stderr('Option "%s" is unknown, try "ip -help".' % opt)
            exit(-1)

    if argv:
        return do_obj(argv, option)

    usage()


if __name__ == '__main__':
    main()
