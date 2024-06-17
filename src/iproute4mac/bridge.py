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
Usage: bridge [ OPTIONS ] OBJECT { COMMAND | help }
       bridge [ -force ] -batch filename
where  OBJECT := { link | fdb | mdb | vlan | vni | monitor }
       OPTIONS := { -V[ersion] | -s[tatistics] | -d[etails] |
                    -o[neline] | -t[imestamp] | -n[etns] name |
                    -com[pressvlans] -c[olor] -p[retty] -j[son] }""")
    exit(-1)


''' Implemented objects '''
objs = [
    ('link', do_notimplemented),
    ('fdb', do_notimplemented),
    ('mdb', do_notimplemented),
    ('vlan', do_notimplemented),
    ('vni', do_notimplemented),
    ('monitor', do_notimplemented),
    ('help', do_help)
]


def do_obj(argv, option):
    obj = argv.pop(0)
    for o, f in objs:
        if o.startswith(obj):
            return f(argv, option)

    stderr('Object "%s" is unknown, try "bridge help".' % obj)
    return EXIT_FAILURE


def main():
    batch_file = None
    option = {
        'preferred_family': AF_UNSPEC,
        'show_stats': False,
        'show_details': False,
        'oneline': False,
        'timestamp': False,
        'compress_vlans': False,
        'force': False,
        'json': False,
        'pretty': False,
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

        if '-help'.startswith(opt):
            usage()
        elif '-Version'.startswith(opt):
            print('bridge wrapper, iproute4mac-%s' % VERSION)
            exit(0)
        elif '-stats'.startswith(opt) or '-statistics'.startswith(opt):
            option['show_stats'] = True
        elif '-details'.startswith(opt):
            option['show_details'] = True
        elif '-oneline'.startswith(opt):
            option['oneline'] = True
        elif '-timestamp'.startswith(opt):
            option['timestamp'] = True
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
        elif '-netns'.startswith(opt):
            do_notimplemented()
        elif matches_color(opt):
            # Color option is not implemented
            pass
        elif '-compressvlans'.startswith(opt):
            option['compress_vlans'] = True
        elif '-force'.startswith(opt):
            option['force'] = True
        elif '-json'.startswith(opt):
            option['json'] = True
        elif '-pretty'.startswith(opt):
            option['pretty'] = True
        elif '-batch'.startswith(opt):
            try:
                batch_file = argv.pop(0)
            except IndexError:
                missarg('batch file')
        else:
            stderr('Option "%s" is unknown, try "bridge help".' % opt)
            exit(-1)

    if argv:
        return do_obj(argv, option)

    usage()


if __name__ == '__main__':
    main()
