import iproute4mac.data as data
import iproute4mac.ifconfig as ifconfig
import iproute4mac.libc as libc
import iproute4mac.utils as utils

from iproute4mac import OPTION
from iproute4mac.utils import matches, strcmp, next_arg


def usage():
    utils.stderr("""\
Usage: bridge fdb { add | append | del | replace } ADDR dev DEV
              [ self ] [ master ] [ use ] [ router ] [ extern_learn ]
              [ sticky ] [ local | static | dynamic ] [ vlan VID ]
              { [ dst IPADDR ] [ port PORT] [ vni VNI ] | [ nhid NHID ] }
              [ via DEV ] [ src_vni VNI ]
       bridge fdb [ show [ br BRDEV ] [ brport DEV ] [ vlan VID ]
              [ state STATE ] [ dynamic ] ]
       bridge fdb get [ to ] LLADDR [ br BRDEV ] { brport | dev } DEV
              [ vlan VID ] [ vni VNI ] [ self ] [ master ] [ dynamic ]
       bridge fdb flush dev DEV [ brport DEV ] [ vlan VID ]
              [ self ] [ master ] [ [no]permanent | [no]static | [no]dynamic ]
              [ [no]added_by_user ] [ [no]extern_learn ] [ [no]sticky ]
              [ [no]offloaded ]""")
    exit(libc.EXIT_ERROR)


def brfdb_modify(argv):
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


def brfdb_list(argv):
    entries = ifconfig.FDB()
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "brport", "dev"):
            dev = next_arg(argv)
            entries.set([e for e in entries if e["ifname"] == dev])
            data.delete_keys(entries, "ifname")
        elif strcmp(opt, "br"):
            dev = next_arg(argv)
            entries.set([e for e in entries if e.bridge == dev])
        elif strcmp(opt, "vlan"):
            vlan_id = next_arg(argv)
            try:
                vlan_id = int(vlan_id)
                assert 0 <= vlan_id < 2**12
            except (ValueError, AssertionError):
                utils.invarg(f'Invalid "{opt}" value', vlan_id)
            entries.set([e for e in entries if e["vlan"] == vlan_id])
        else:
            if matches(opt, "help"):
                usage()

    utils.output(entries)

    return libc.EXIT_SUCCESS


def do_brfdb(argv):
    if not argv:
        return brfdb_list(argv)

    cmd = argv.pop(0)
    if matches(cmd, "add", "append", "replace", "delete"):
        return brfdb_modify(cmd, argv)
    elif matches(cmd, "show", "lst", "list"):
        return brfdb_list(argv)
    elif matches(cmd, "help"):
        return usage()

    utils.stderr(f'Command "{cmd}" is unknown, try "bridge fdb help".')
    exit(libc.EXIT_ERROR)
