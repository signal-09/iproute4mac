import iproute4mac.nud as nud

from iproute4mac.utils import *


def usage():
    stderr("""\
Usage: ip neigh { add | del | change | replace }
                { ADDR [ lladdr LLADDR ] [ nud STATE ] proxy ADDR }
                [ dev DEV ] [ router ] [ extern_learn ] [ protocol PROTO ]

       ip neigh { show | flush } [ proxy ] [ to PREFIX ] [ dev DEV ] [ nud STATE ]
                                 [ vrf NAME ]

       ip neigh get { ADDR | proxy ADDR } dev DEV

STATE := { delay | failed | incomplete | noarp | none |
           permanent | probe | reachable | stale }""")
    exit(-1)


def ipneigh_modify(cmd, argv):
    entries = nud.Nud()
    dev = None
    lla = None
    dst = None
    states = []
    while argv:
        opt = argv.pop(0)
        if matches(opt, "lladdr"):
            opt = next_arg(argv)
            if lla:
                duparg("lladdr", opt)
            lla = opt
            entries.set([e for e in entries if e["lladdr"] == lla])
        elif strcmp(opt, "nud"):
            state = next_arg(argv)
            if strcmp(state, "all"):
                # FIXME: NOARP not catched
                continue
            try:
                state = nud.from_string(state)
            except ValueError:
                invarg("nud state is bad", state)
            states.append(nud.to_state(state))
        elif matches(opt, "proxy"):
            opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            if dst:
                duparg("address", opt)
            dst = get_addr(opt, OPTION["preferred_family"])
        elif strcmp(opt, "router"):
            entries.set([e for e in entries if "router" in e])
        elif matches(opt, "extern_learn"):
            do_notimplemented(opt)
        elif strcmp(opt, "dev"):
            opt = next_arg(argv)
            if dev:
                duparg("dev", opt)
            dev = opt
            entries.set([e for e in entries if e["dev"] == dev])
        elif matches(opt, "protocol"):
            do_notimplemented(opt)
        else:
            if strcmp(opt, "to"):
                opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            if dst:
                duparg2("to", opt)
            try:
                dst = get_addr(opt, OPTION["preferred_family"])
            except ValueError:
                invarg("to value is invalid", opt)
            entries.set([e for e in entries if e["dst"] in dst])

    if not dev or not dst:
        stderr("Device and destination are required arguments.")
        exit(-1)

    if OPTION["preferred_family"] != AF_UNSPEC:
        entries.set([e for e in entries if e["dst"].family == OPTION["preferred_family"]])

    if states:
        entries.set([e for e in entries if set(e["state"]) <= set(states)])

    if matches(cmd, "add"):
        do_notimplemented()
    elif matches(cmd, "change"):
        do_notimplemented()
    elif matches(cmd, "replace"):
        do_notimplemented()
    elif matches(cmd, "delete"):
        for entry in entries:
            nud.delete(entry["dst"], dev=entry["dev"])
    else:
        do_notimplemented()

    return EXIT_SUCCESS


def ipneigh_get(argv):
    entries = nud.Nud()
    dev = None
    dst = None
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "dev"):
            opt = next_arg(argv)
            if dev:
                duparg("dev", opt)
            dev = opt
            entries.set([e for e in entries if e["dev"] == dev])
        elif strcmp(opt, "proxy"):
            entries.set([e for e in entries if "proxy" in e["state"]])
        else:
            if strcmp(opt, "to"):
                opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            if dst:
                duparg2("to", opt)
            try:
                dst = get_addr(opt, OPTION["preferred_family"])
            except ValueError:
                invarg("to value is invalid", opt)
            entries.set([e for e in entries if e["dst"] == dst])

    if not dev or not dst:
        stderr("Device and address are required arguments.")
        return EXIT_FAILURE

    OPTION["json"] = False
    output(entries)

    return EXIT_SUCCESS


def ipneigh_list_or_flush(argv, flush=False):
    if flush and not argv:
        stderr("Flush requires arguments.")
        exit(-1)

    entries = nud.Nud()
    dev = None
    states = []
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "dev"):
            opt = next_arg(argv)
            if dev:
                duparg("dev", opt)
            dev = opt
            entries.set([e for e in entries if e["dev"] == dev])
            if not flush:
                delete_keys(entries, "dev")
        elif strcmp(opt, "master"):
            opt = next_arg(argv)
            warn("Kernel does not support filtering by master device")
        elif strcmp(opt, "vrf"):
            do_notimplemented(opt)
        elif strcmp(opt, "unused"):
            entries.set([e for e in entries if e.unused])
        elif strcmp(opt, "nud"):
            state = next_arg(argv)
            if strcmp(state, "all"):
                # FIXME: NOARP not catched
                continue
            try:
                state = nud.from_string(state)
            except ValueError:
                invarg("nud state is bad", state)
            states.append(nud.to_state(state))
        elif strcmp(opt, "proxy"):
            entries.set([e for e in entries if "proxy" in e["state"]])
        elif matches(opt, "protocol"):
            do_notimplemented(opt)
        else:
            if strcmp(opt, "to"):
                opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            try:
                prefix = get_addr(opt, OPTION["preferred_family"])
            except ValueError:
                invarg("to value is invalid", opt)
            entries.set([e for e in entries if e["dst"] in prefix])

    if OPTION["preferred_family"] != AF_UNSPEC:
        entries.set([e for e in entries if e["dst"].family == OPTION["preferred_family"]])

    if states:
        entries.set([e for e in entries if set(e["state"]) <= set(states)])

    if flush:
        for entry in entries:
            nud.delete(entry["dst"], dev=entry["dev"])
    else:
        output(entries)

    return EXIT_SUCCESS


def do_ipneigh(argv):
    if not argv:
        return ipneigh_list_or_flush(argv)

    cmd = argv.pop(0)
    if matches(cmd, "add", "change", "replace", "delete") or strcmp(cmd, "chg"):
        return ipneigh_modify(cmd, argv)
    elif matches(cmd, "get"):
        return ipneigh_get(argv)
    elif matches(cmd, "show", "lst", "list"):
        return ipneigh_list_or_flush(argv)
    elif matches(cmd, "flush"):
        return ipneigh_list_or_flush(argv, flush=True)
    elif matches(cmd, "help"):
        usage()

    stderr(f'Command "{cmd}" is unknown, try "ip neigh help".')
    exit(-1)
