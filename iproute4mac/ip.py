#!/usr/bin/env python3

import os
import sys
import iproute4mac

from iproute4mac.utils import *
from iproute4mac.iplink import do_iplink
from iproute4mac.ipaddress import do_ipaddr
from iproute4mac.iproute import do_iproute


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


""" Implemented objects """
objs = [
    ("address", do_ipaddr),
    ("addrlabel", do_notimplemented),
    ("maddress", do_notimplemented),
    ("route", do_iproute),
    ("rule", do_notimplemented),
    ("neighbor", do_notimplemented),
    ("neighbour", do_notimplemented),
    ("ntable", do_notimplemented),
    ("ntbl", do_notimplemented),
    ("link", do_iplink),
    ("l2tp", do_notimplemented),
    ("fou", do_notimplemented),
    ("ila", do_notimplemented),
    ("macsec", do_notimplemented),
    ("tunnel", do_notimplemented),
    ("tunl", do_notimplemented),
    ("tuntap", do_notimplemented),
    ("tap", do_notimplemented),
    ("token", do_notimplemented),
    ("tcpmetrics", do_notimplemented),
    ("tcp_metrics", do_notimplemented),
    ("monitor", do_notimplemented),
    ("xfrm", do_notimplemented),
    ("mroute", do_notimplemented),
    ("mrule", do_notimplemented),
    ("netns", do_notimplemented),
    ("netconf", do_notimplemented),
    ("vrf", do_notimplemented),
    ("sr", do_notimplemented),
    ("nexthop", do_notimplemented),
    ("mptcp", do_notimplemented),
    ("ioam", do_notimplemented),
    ("help", do_help),
    ("stats", do_notimplemented),
]


def do_obj(argv, option):
    obj = argv.pop(0)
    for o, f in objs:
        if o.startswith(obj):
            return f(argv, option)

    stderr(f'Object "{obj}" is unknown, try "ip help".')
    return EXIT_FAILURE


def main():
    batch_file = None
    option = {
        "preferred_family": AF_UNSPEC,
        "human_readable": False,
        "use_iec": False,
        "show_stats": False,
        "show_details": False,
        "oneline": False,
        "brief": False,
        "json": False,
        "pretty": False,
        "timestamp": False,
        "timestamp_short": False,
        "echo_request": False,
        "force": False,
        "max_flush_loops": 10,
        "batch_mode": False,
        "do_all": False,
        "uid": os.getuid(),
        "verbose": 0,
    }

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

        if matches(opt, "-loops"):
            try:
                option["max_flush_loops"] = int(argv.pop(0))
            except IndexError:
                missarg("loop count")
            except ValueError:
                error("loop count not a number")
        elif matches(opt, "-family"):
            try:
                opt = argv.pop(0)
            except IndexError:
                missarg("family type")
            if strcmp(opt, "help"):
                usage()
            option["preferred_family"] = read_family(opt)
            if option["preferred_family"] == AF_UNSPEC:
                invarg("invalid protocol family", opt)
        elif strcmp(opt, "-4"):
            option["preferred_family"] = AF_INET
        elif strcmp(opt, "-6"):
            option["preferred_family"] = AF_INET6
        elif strcmp(opt, "-0"):
            option["preferred_family"] = AF_PACKET
        elif strcmp(opt, "-M"):
            option["preferred_family"] = AF_MPLS
        elif strcmp(opt, "-B"):
            option["preferred_family"] = AF_BRIDGE
        elif matches(opt, "-human-readable"):
            option["human_readable"] = True
        elif matches(opt, "-iec"):
            option["use_iec"] = True
        elif matches(opt, "-stats", "-statistics"):
            option["show_stats"] = True
        elif matches(opt, "-details"):
            option["show_details"] = True
        elif matches(opt, "-resolve"):
            option["resolve_hosts"] = True
        elif matches(opt, "-oneline"):
            option["oneline"] = True
        elif matches(opt, "-timestamp"):
            option["timestamp"] = True
        elif matches(opt, "-tshort"):
            option["timestamp"] = True
            option["timestamp_short"] = True
        elif matches(opt, "-Version"):
            print(f"ip wrapper, iproute4mac-{iproute4mac.VERSION}")
            exit(0)
        elif matches(opt, "-force"):
            option["force"] = True
        elif matches(opt, "-batch"):
            try:
                batch_file = argv.pop(0)
            except IndexError:
                missarg("batch file")
        elif matches(opt, "-brief"):
            option["brief"] = True
        elif matches(opt, "-json"):
            option["json"] = True
        elif matches(opt, "-pretty"):
            option["pretty"] = True
        elif matches(opt, "-rcvbuf"):
            try:
                option["rcvbuf"] = int(argv.pop(0))
            except IndexError:
                missarg("rcvbuf size")
            except ValueError:
                error("rcvbuf size not a number")
        elif matches_color(opt):
            # Color option is not implemented
            pass
        elif matches(opt, "-help"):
            usage()
        elif matches(opt, "-netns"):
            do_notimplemented()
        elif matches(opt, "-Numeric"):
            option["numeric"] = True
        elif matches(opt, "-all"):
            option["do_all"] = True
        elif strcmp(opt, "-echo"):
            option["echo_request"] = True
        elif strcmp(opt, "-verbose"):
            option["verbose"] += 1
        else:
            stderr(f'Option "{opt}" is unknown, try "ip -help".')
            exit(-1)

    if batch_file:
        do_notimplemented()

    if argv:
        return do_obj(argv, option)

    usage()


if __name__ == "__main__":
    main()
