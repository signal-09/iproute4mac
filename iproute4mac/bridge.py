#!/usr/bin/env python3

from iproute4mac.utils import *


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


# Implemented objects
OBJS = [
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
    for o, f in OBJS:
        if o.startswith(obj):
            return f(argv)

    stderr(f'Object "{obj}" is unknown, try "bridge help".')
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

        if matches(opt, "-help"):
            usage()
        elif matches(opt, "-Version"):
            print(f"bridge wrapper, iproute4mac-{VERSION}")
            exit(0)
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
        elif matches(opt, "-netns"):
            do_notimplemented()
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
                missarg("batch file")
        elif matches(opt, "-verbose", "-vvv"):
            while opt[1] == "v" and OPTION["verbose"] < LOG_DEBUG:
                OPTION["verbose"] += 1
                if len(opt) <= 2:
                    break
                opt = opt[1:]
        elif matches(opt, "-quiet"):
            OPTION["quiet"] = True
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
