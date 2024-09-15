#!/usr/bin/env python3

import iproute4mac
import os
import sys

import iproute4mac.brlink as brlink
import iproute4mac.brfdb as brfdb
import iproute4mac.libc as libc
import iproute4mac.socket as socket
import iproute4mac.utils as utils

from iproute4mac import __version__, OPTION
from iproute4mac.utils import matches, strcmp, matches_color


OPTION["uid"] = os.getuid()


def do_help(argv=[]):
    usage()


def usage():
    utils.stderr("""\
Usage: bridge [ OPTIONS ] OBJECT { COMMAND | help }
       bridge [ -force ] -batch filename
where  OBJECT := { link | fdb | mdb | vlan | vni | monitor }
       OPTIONS := { -V[ersion] | -s[tatistics] | -d[etails] |
                    -o[neline] | -t[imestamp] | -n[etns] name |
                    -com[pressvlans] -c[olor] -p[retty] -j[son] }""")
    exit(libc.EXIT_ERROR)


# Implemented objects
OBJS = [
    ("link", brlink.do_brlink),
    ("fdb", brfdb.do_brfdb),
    ("mdb", utils.do_notimplemented),
    ("vlan", utils.do_notimplemented),
    ("vni", utils.do_notimplemented),
    ("monitor", utils.do_notimplemented),
    ("help", do_help),
]


def do_obj(argv):
    obj = argv.pop(0)
    for o, f in OBJS:
        if o.startswith(obj):
            return f(argv)

    utils.stderr(f'Object "{obj}" is unknown, try "bridge help".')
    return libc.EXIT_FAILURE


def main():
    if sys.platform != "darwin":
        utils.stderr("Unupported OS.")
        exit(libc.EXIT_ERROR)

    batch_file = None
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

        if matches(opt, "-help"):
            usage()
        elif matches(opt, "-Version"):
            print(f"bridge wrapper, iproute4mac-{__version__}")
            exit(libc.EXIT_SUCCESS)
        elif matches(opt, "-stats".startswith(opt) or "-statistics"):
            OPTION["show_stats"] = True
        elif matches(opt, "-details"):
            OPTION["show_details"] = True
        elif matches(opt, "-oneline"):
            OPTION["oneline"] = True
        elif matches(opt, "-timestamp"):
            OPTION["timestamp"] = True
        elif matches(opt, "-family"):
            try:
                opt = argv.pop(0)
            except IndexError:
                utils.missarg("family type")
            if strcmp(opt, "help"):
                usage()
            OPTION["preferred_family"] = socket.read_family(opt)
            if OPTION["preferred_family"] == socket._AF_UNSPEC:
                utils.invarg("invalid protocol family", opt)
        elif strcmp(opt, "-4"):
            OPTION["preferred_family"] = socket._AF_INET
        elif strcmp(opt, "-6"):
            OPTION["preferred_family"] = socket._AF_INET6
        elif matches(opt, "-netns"):
            utils.do_notimplemented()
        elif matches_color(opt):
            # silently ignore not implemented color option
            pass
        elif matches(opt, "-compressvlans"):
            OPTION["compress_vlans"] = True
        elif matches(opt, "-force"):
            OPTION["force"] = True
        elif matches(opt, "-json"):
            OPTION["json"] = True
        elif matches(opt, "-pretty"):
            OPTION["pretty"] = True
        elif matches(opt, "-batch"):
            try:
                batch_file = argv.pop(0)
            except IndexError:
                utils.missarg("batch file")
        elif matches(opt, "-verbose", "-vvv"):
            while opt[1] == "v" and OPTION["verbose"] < utils.LOG_DEBUG:
                OPTION["verbose"] += 1
                if len(opt) <= 2:
                    break
                opt = opt[1:]
        elif matches(opt, "-silent"):
            OPTION["verbose"] = utils.LOG_STDERR
        elif matches(opt, "-quiet"):
            OPTION["verbose"] = -1
        elif matches(opt, "-debug"):
            pass
        else:
            utils.stderr(f'Option "{opt}" is unknown, try "bridge help".')
            exit(libc.EXIT_ERROR)

    if batch_file:
        utils.do_notimplemented()

    if argv:
        return do_obj(argv)

    usage()


if __name__ == "__main__":
    main()
