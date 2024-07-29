#!/usr/bin/env python3

import sys

import iproute4mac
from iproute4mac.utils import *
from iproute4mac.iplink import *
from iproute4mac.ipaddress import *


def do_help(argv=[]):
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


""" Implemented objects """
objs = [
    ("link", do_notimplemented),
    ("fdb", do_notimplemented),
    ("mdb", do_notimplemented),
    ("vlan", do_notimplemented),
    ("vni", do_notimplemented),
    ("monitor", do_notimplemented),
    ("help", do_help),
]


def do_obj(argv):
    obj = argv.pop(0)
    for o, f in objs:
        if o.startswith(obj):
            return f(argv)

    stderr(f'Object "{obj}" is unknown, try "bridge help".')
    return EXIT_FAILURE


def main():
    batch_file = None

    if sys.platform != "darwin":
        stderr("Unupported OS.")
        exit(-1)

    argv = sys.argv[1:]
    while argv:
        if argv[0] == "--":
            argv.pop(0)
            break
        elif argv[0][0] != "-":
            break

        opt = argv.pop(0)
        if opt[1] == "-":
            opt = opt[1:]

        if "-help".startswith(opt):
            usage()
        elif "-Version".startswith(opt):
            print(f"bridge wrapper, iproute4mac-{iproute4mac.VERSION}")
            exit(0)
        elif "-stats".startswith(opt) or "-statistics".startswith(opt):
            OPTION["show_stats"] = True
        elif "-details".startswith(opt):
            OPTION["show_details"] = True
        elif "-oneline".startswith(opt):
            OPTION["oneline"] = True
        elif "-timestamp".startswith(opt):
            OPTION["timestamp"] = True
        elif "-family".startswith(opt):
            try:
                opt = argv.pop(0)
            except IndexError:
                missarg("family type")
            if opt == "help":
                usage()
            OPTION["preferred_family"] = read_family(opt)
            if OPTION["preferred_family"] == AF_UNSPEC:
                invarg("invalid protocol family", opt)
        elif opt == "-4":
            OPTION["preferred_family"] = AF_INET
        elif opt == "-6":
            OPTION["preferred_family"] = AF_INET6
        elif "-netns".startswith(opt):
            do_notimplemented()
        elif matches_color(opt):
            # Color option is not implemented
            pass
        elif "-compressvlans".startswith(opt):
            OPTION["compress_vlans"] = True
        elif "-force".startswith(opt):
            OPTION["force"] = True
        elif "-json".startswith(opt):
            OPTION["json"] = True
        elif "-pretty".startswith(opt):
            OPTION["pretty"] = True
        elif "-batch".startswith(opt):
            try:
                batch_file = argv.pop(0)
            except IndexError:
                missarg("batch file")
        else:
            stderr(f'Option "{opt}" is unknown, try "bridge help".')
            exit(-1)

    if batch_file:
        do_notimplemented()

    if argv:
        return do_obj(argv)

    usage()


if __name__ == "__main__":
    main()
