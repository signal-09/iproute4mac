import iproute4mac.libc as libc
import iproute4mac.utils as utils

from iproute4mac.ipaddress import get_ifconfig_links
from iproute4mac.utils import matches, strcmp, next_arg


def usage():
    utils.stderr("""\
Usage: bridge link set dev DEV [ cost COST ] [ priority PRIO ] [ state STATE ]
                               [ guard {on | off} ]
                               [ hairpin {on | off} ]
                               [ fastleave {on | off} ]
                               [ root_block {on | off} ]
                               [ learning {on | off} ]
                               [ learning_sync {on | off} ]
                               [ flood {on | off} ]
                               [ mcast_router MULTICAST_ROUTER ]
                               [ mcast_flood {on | off} ]
                               [ bcast_flood {on | off} ]
                               [ mcast_to_unicast {on | off} ]
                               [ neigh_suppress {on | off} ]
                               [ vlan_tunnel {on | off} ]
                               [ isolated {on | off} ]
                               [ locked {on | off} ]
                               [ hwmode {vepa | veb} ]
                               [ backup_port DEVICE ] [ nobackup_port ]
                               [ self ] [ master ]
       bridge link show [dev DEV]""")
    exit(libc.EXIT_ERROR)


def brlink_modify(argv):
    return libc.EXIT_SUCCESS


def brlink_list(argv):
    dev = None
    links = get_ifconfig_links(argv)
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "dev"):
            opt = next_arg(argv)
            if dev:
                utils.duparg2("dev", opt)
            if not links.exist(opt):
                utils.stderr(f'Cannot find device "{opt}"')
                exit(libc.EXIT_ERROR)
            dev = opt
            links.set([l for l in links if l.ifname == dev])

    utils.output(links)

    return libc.EXIT_SUCCESS


def do_brlink(argv):
    if not argv:
        return brlink_list(argv)

    cmd = argv.pop(0)
    if matches(cmd, "set", "change"):
        return brlink_modify(argv)
    elif matches(cmd, "show", "lst", "list"):
        return brlink_list(argv)
    elif matches(cmd, "help"):
        return usage()

    utils.stderr(f'Command "{cmd}" is unknown, try "bridge link help".')
    exit(libc.EXIT_ERROR)
