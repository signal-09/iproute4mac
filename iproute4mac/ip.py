#!/usr/bin/env python3

from iproute4mac.utils import *
from iproute4mac.iplink import do_iplink
from iproute4mac.ipaddress import do_ipaddr
from iproute4mac.iproute import do_iproute
from iproute4mac.ipneigh import do_ipneigh


def do_help(argv=[]):
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


# Implemented objects
OBJS = [
    ("address", do_ipaddr),
    ("addrlabel", do_notimplemented),
    ("maddress", do_notimplemented),
    ("route", do_iproute),
    ("rule", do_notimplemented),
    ("neighbor", do_ipneigh),
    ("neighbour", do_ipneigh),
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


def do_obj(argv):
    obj = argv.pop(0)
    for o, f in OBJS:
        if o.startswith(obj):
            return f(argv)

    stderr(f'Object "{obj}" is unknown, try "ip help".')
    return EXIT_FAILURE


def main():
    if sys.platform != "darwin":
        stderr("Unupported OS.")
        exit(-1)

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
            OPTION["preferred_family"] = read_family(opt)
            if OPTION["preferred_family"] == AF_UNSPEC:
                invarg("invalid protocol family", opt)
        elif strcmp(opt, "-4"):
            OPTION["preferred_family"] = AF_INET
        elif strcmp(opt, "-6"):
            OPTION["preferred_family"] = AF_INET6
        elif strcmp(opt, "-0"):
            OPTION["preferred_family"] = AF_PACKET
        elif strcmp(opt, "-M"):
            OPTION["preferred_family"] = AF_MPLS
        elif strcmp(opt, "-B"):
            OPTION["preferred_family"] = AF_BRIDGE
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
            print(f"ip wrapper, iproute4mac-{VERSION}")
            exit(0)
        elif matches(opt, "-force"):
            OPTION["force"] = True
        elif matches(opt, "-batch"):
            try:
                batch_file = argv.pop(0)
            except IndexError:
                missarg("batch file")
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
                missarg("rcvbuf size")
            except ValueError:
                error("rcvbuf size not a number")
        elif matches_color(opt):
            # silently ignore not implemented color option
            pass
        elif matches(opt, "-help"):
            usage()
        elif matches(opt, "-netns"):
            do_notimplemented()
        elif matches(opt, "-Numeric"):
            OPTION["numeric"] = True
        elif matches(opt, "-all"):
            OPTION["do_all"] = True
        elif strcmp(opt, "-echo"):
            OPTION["echo_request"] = True
        elif matches(opt, "-verbose", "-vvv"):
            while opt[1] == "v" and OPTION["verbose"] < LOG_DEBUG:
                OPTION["verbose"] += 1
                if len(opt) <= 2:
                    break
                opt = opt[1:]
        elif matches(opt, "-quiet"):
            OPTION["quiet"] = True
        else:
            stderr(f'Option "{opt}" is unknown, try "ip -help".')
            exit(-1)

    if batch_file:
        do_notimplemented()

    if argv:
        return do_obj(argv)

    usage()


if __name__ == "__main__":
    main()
