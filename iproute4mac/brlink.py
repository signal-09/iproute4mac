import iproute4mac.ifconfig as ifconfig
import iproute4mac.libc as libc
import iproute4mac.utils as utils

from iproute4mac import OPTION
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
    dev = None
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "dev"):
            dev = next_arg(argv)
        elif strcmp(opt, "guard"):
            guard = next_arg(argv)
            utils.parse_on_off(opt, guard)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "hairpin"):
            hairpin = next_arg(argv)
            utils.parse_on_off(opt, hairpin)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "fastleave"):
            fastleave = next_arg(argv)
            utils.parse_on_off(opt, fastleave)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "root_block"):
            root_block = next_arg(argv)
            utils.parse_on_off(opt, root_block)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "learning"):
            learning = next_arg(argv)
            utils.parse_on_off(opt, learning)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "learning_sync"):
            learning_sync = next_arg(argv)
            utils.parse_on_off(opt, learning_sync)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "flood"):
            flood = next_arg(argv)
            utils.parse_on_off(opt, flood)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "mcast_flood"):
            mcast_flood = next_arg(argv)
            utils.parse_on_off(opt, mcast_flood)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "mcast_to_unicast"):
            mcast_to_unicast = next_arg(argv)
            utils.parse_on_off(opt, mcast_to_unicast)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "cost"):
            cost = next_arg(argv)
            try:
                cost = int(cost)
            except ValueError:
                utils.invarg(f'Invalid "{opt}" value', cost)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "priority"):
            priority = next_arg(argv)
            try:
                priority = int(priority)
            except ValueError:
                utils.invarg(f'Invalid "{opt}" value', priority)
            utils.do_notimplemented(opt)
        else:
            usage()

    if not dev:
        utils.stderr("Device is a required argument.")
        exit(libc.EXIT_ERROR)

    return libc.EXIT_SUCCESS


def brlink_list(argv):
    dev = None
    links = ifconfig.Bridge()
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
            links.set([i for i in links if i.name == dev])

    if not OPTION["show_details"]:
        links.set([i for i in links if i.link != i])

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
