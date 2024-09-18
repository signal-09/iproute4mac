#!/usr/bin/env python3

import iproute4mac
import os
import sys

import iproute4mac.debug as debug
import iproute4mac.ipaddress as ipaddress
import iproute4mac.iplink as iplink
import iproute4mac.ipneigh as ipneigh
import iproute4mac.iproute as iproute
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
    exit(libc.EXIT_ERROR)


# Implemented objects
OBJS = [
    ("address", ipaddress.do_ipaddr),
    ("addrlabel", utils.do_notimplemented),
    ("maddress", utils.do_notimplemented),
    ("route", iproute.do_iproute),
    ("rule", utils.do_notimplemented),
    ("neighbor", ipneigh.do_ipneigh),
    ("neighbour", ipneigh.do_ipneigh),
    ("ntable", utils.do_notimplemented),
    ("ntbl", utils.do_notimplemented),
    ("link", iplink.do_iplink),
    ("l2tp", utils.do_notimplemented),
    ("fou", utils.do_notimplemented),
    ("ila", utils.do_notimplemented),
    ("macsec", utils.do_notimplemented),
    ("tunnel", utils.do_notimplemented),
    ("tunl", utils.do_notimplemented),
    ("tuntap", utils.do_notimplemented),
    ("tap", utils.do_notimplemented),
    ("token", utils.do_notimplemented),
    ("tcpmetrics", utils.do_notimplemented),
    ("tcp_metrics", utils.do_notimplemented),
    ("monitor", utils.do_notimplemented),
    ("xfrm", utils.do_notimplemented),
    ("mroute", utils.do_notimplemented),
    ("mrule", utils.do_notimplemented),
    ("netns", utils.do_notimplemented),
    ("netconf", utils.do_notimplemented),
    ("vrf", utils.do_notimplemented),
    ("sr", utils.do_notimplemented),
    ("nexthop", utils.do_notimplemented),
    ("mptcp", utils.do_notimplemented),
    ("ioam", utils.do_notimplemented),
    ("help", do_help),
    ("stats", utils.do_notimplemented),
    ("debug", debug.do_debug),
]


def do_obj(argv):
    obj = argv.pop(0)
    for o, f in OBJS:
        if o.startswith(obj):
            return f(argv)

    utils.stderr(f'Object "{obj}" is unknown, try "ip help".')
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

        if matches(opt, "-loops"):
            try:
                OPTION["max_flush_loops"] = int(argv.pop(0))
            except IndexError:
                utils.missarg("loop count")
            except ValueError:
                utils.error("loop count not a number")
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
        elif strcmp(opt, "-0"):
            OPTION["preferred_family"] = socket._AF_PACKET
        elif strcmp(opt, "-M"):
            OPTION["preferred_family"] = socket._AF_MPLS
        elif strcmp(opt, "-B"):
            OPTION["preferred_family"] = socket._AF_BRIDGE
        elif matches(opt, "-human-readable"):
            OPTION["human_readable"] = True
        elif matches(opt, "-iec"):
            OPTION["use_iec"] = True
        elif matches(opt, "-stats", "-statistics"):
            OPTION["show_stats"] = True
        elif matches(opt, "-details"):
            OPTION["show_details"] = True
        elif matches(opt, "-resolve"):
            OPTION["resolve_hosts"] = True
        elif matches(opt, "-oneline"):
            OPTION["oneline"] = True
        elif matches(opt, "-timestamp"):
            OPTION["timestamp"] = True
        elif matches(opt, "-tshort"):
            OPTION["timestamp"] = True
            OPTION["timestamp_short"] = True
        elif matches(opt, "-Version"):
            print(f"ip wrapper, iproute4mac-{__version__}")
            exit(libc.EXIT_SUCCESS)
        elif matches(opt, "-force"):
            OPTION["force"] = True
        elif matches(opt, "-batch"):
            try:
                batch_file = argv.pop(0)
            except IndexError:
                utils.missarg("batch file")
        elif matches(opt, "-brief"):
            OPTION["brief"] = True
        elif matches(opt, "-json"):
            OPTION["json"] = True
        elif matches(opt, "-pretty"):
            OPTION["pretty"] = True
        elif matches(opt, "-rcvbuf"):
            try:
                OPTION["rcvbuf"] = int(argv.pop(0))
            except IndexError:
                utils.missarg("rcvbuf size")
            except ValueError:
                utils.error("rcvbuf size not a number")
        elif matches_color(opt):
            # silently ignore not implemented color option
            pass
        elif matches(opt, "-help"):
            usage()
        elif matches(opt, "-netns"):
            utils.do_notimplemented()
        elif matches(opt, "-Numeric"):
            OPTION["numeric"] = True
        elif matches(opt, "-all"):
            OPTION["do_all"] = True
        elif strcmp(opt, "-echo"):
            OPTION["echo_request"] = True
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
            debug.all()
        else:
            utils.stderr(f'Option "{opt}" is unknown, try "ip -help".')
            exit(libc.EXIT_ERROR)

    if batch_file:
        utils.do_notimplemented()

    if argv:
        return do_obj(argv)

    usage()


if __name__ == "__main__":
    main()
