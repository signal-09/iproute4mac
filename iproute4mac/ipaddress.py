import iproute4mac.ifconfig as ifconfig

from iproute4mac.utils import *


FLAG_MASK = [
    "secondary",
    "temporary",
    "nodad",
    "optimistic",
    "dadfailed",
    "home",
    "deprecated",
    "tentative",
    "permanent",
    "mngtmpaddr",
    "noprefixroute",
    "autojoin",
    "stable-privacy",
]


def usage():
    stderr("""\
Usage: ip address {add|change|replace} IFADDR dev IFNAME [ LIFETIME ]
                                                      [ CONFFLAG-LIST ]
       ip address del IFADDR dev IFNAME [mngtmpaddr]
       ip address {save|flush} [ dev IFNAME ] [ scope SCOPE-ID ]
                            [ to PREFIX ] [ FLAG-LIST ] [ label LABEL ] [up]
       ip address [ show [ dev IFNAME ] [ scope SCOPE-ID ] [ master DEVICE ]
                         [ nomaster ]
                         [ type TYPE ] [ to PREFIX ] [ FLAG-LIST ]
                         [ label LABEL ] [up] [ vrf NAME ]
                         [ proto ADDRPROTO ] ]
       ip address {showdump|restore}
IFADDR := PREFIX | ADDR peer PREFIX
          [ broadcast ADDR ] [ anycast ADDR ]
          [ label IFNAME ] [ scope SCOPE-ID ] [ metric METRIC ]
          [ proto ADDRPROTO ]
SCOPE-ID := [ host | link | global | NUMBER ]
FLAG-LIST := [ FLAG-LIST ] FLAG
FLAG  := [ permanent | dynamic | secondary | primary |
           [-]tentative | [-]deprecated | [-]dadfailed | temporary |
           CONFFLAG-LIST ]
CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG
CONFFLAG  := [ home | nodad | mngtmpaddr | noprefixroute | autojoin ]
LIFETIME := [ valid_lft LFT ] [ preferred_lft LFT ]
LFT := forever | SECONDS
ADDRPROTO := [ NAME | NUMBER ]
TYPE := { amt | bareudp | bond | bond_slave | bridge | bridge_slave |
          dsa | dummy | erspan | geneve | gre | gretap | gtp | hsr |
          ifb | ip6erspan | ip6gre | ip6gretap | ip6tnl |
          ipip | ipoib | ipvlan | ipvtap |
          macsec | macvlan | macvtap | netdevsim |
          netkit | nlmon | pfcp | rmnet | sit | team | team_slave |
          vcan | feth | vlan | vrf | vti | vxcan | vxlan | wwan |
          xfrm | virt_wifi }""")
    exit(-1)


def ipaddr_add(dev, local, broadcast):
    args = ()
    if local:
        address = str(local)
        proto = "inet" if local.version == 4 else "inet6"
    else:
        address = None
        proto = None
    if broadcast:
        if not local or local.family != AF_INET:
            stderr("Broadcast can be set only for IPv4 addresses")
            exit(EXIT_FAILURE)
        if broadcast == "+":
            broadcast = str(local._network.broadcast_address)
        elif broadcast == "-":
            broadcast = str(local._network.network_address)
        else:
            broadcast = str(broadcast)
        args += ("broadcast", broadcast)

    if res := ifconfig.run(dev, proto, address, args, "alias"):
        stdout(res, optional=True)


def ipaddr_del(dev, local):
    if local:
        address = str(local)
        proto = "inet" if local.version == 4 else "inet6"
    else:
        address = None
        proto = None

    if res := ifconfig.run(dev, proto, address, "-alias"):
        stdout(res, optional=True)


def ipaddr_modify(cmd, argv):
    dev = None
    local = None
    peer = None
    broadcast = None
    anycast = None
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "peer", "remote"):
            opt = next_arg(argv)
            if peer:
                duparg("peer", opt)
            peer = get_prefix(opt, OPTION["preferred_family"])
            OPTION["preferred_family"] = peer.family
        elif matches(opt, "broadcast") or strcmp(opt, "brd"):
            opt = next_arg(argv)
            if broadcast:
                duparg("broadcast", opt)
            if strcmp(opt, "+", "-"):
                broadcast = opt
            else:
                broadcast = get_addr(opt, OPTION["preferred_family"])
                OPTION["preferred_family"] = broadcast.family
        elif strcmp(opt, "anycast"):
            opt = next_arg(argv)
            if anycast:
                duparg("anycast", opt)
            anycast = get_addr(opt, OPTION["preferred_family"])
            # FIXME: anycast is supported by ifconfig
            do_notimplemented(opt)
        elif strcmp(opt, "scope"):
            do_notimplemented(opt)
        elif strcmp(opt, "dev"):
            dev = next_arg(argv)
        elif strcmp(opt, "label"):
            do_notimplemented(opt)
        elif matches(opt, "metric", "priority", "preference"):
            metric = next_arg(argv)
            try:
                assert 0 <= int(metric) < 2**32
            except (ValueError, AssertionError):
                invarg('"metric" value is invalid', metric)
            do_notimplemented(opt)
        elif matches(opt, "valid_lft"):
            lft = next_arg(argv)
            hint(f'try "sysctl -w net.inet6.ip6.tempvltime={lft}" instead.')
            do_notimplemented(opt)
        elif matches(opt, "preferred_lft"):
            lft = next_arg(argv)
            hint(f'try "sysctl -w net.inet6.ip6.temppltime={lft}" instead.')
            do_notimplemented(opt)
        elif strcmp(opt, FLAG_MASK):
            do_notimplemented(opt)
        else:
            if strcmp(opt, "local"):
                opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            if local:
                duparg2("local", opt)
            local = get_prefix(opt, OPTION["preferred_family"])
            if "/" not in opt:
                local = Prefix(f"{opt}/{local.max_prefixlen}")
            OPTION["preferred_family"] = local.family

    if not dev:
        stderr('Not enough information: "dev" argument is required.')
        return EXIT_FAILURE

    if matches(cmd, "add", "change", "replace") or strcmp(cmd, "chg"):
        ipaddr_add(dev, local, broadcast)
    elif matches(cmd, "delete"):
        ipaddr_del(dev, local)
    else:
        do_notimplemented()

    return EXIT_SUCCESS


def get_ifconfig_links(argv, usage=usage):
    links = ifconfig.Ifconfig()
    dev = None
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "to"):
            prefix = get_prefix(next_arg(argv), OPTION["preferred_family"])
            if prefix.family != AF_UNSPEC:
                OPTION["preferred_family"] = prefix.family
            for link in links:
                link["addr_info"] = [a for a in link.get("addr_info", []) if a["local"] in prefix]
            links.set([l for l in links if l["addr_info"]])
        elif strcmp(opt, "scope"):
            scope = next_arg(argv)
            if scope not in ("link", "host", "global", "all") and not scope.isdigit():
                invarg('invalid "scope"', scope)
            if scope == "all":
                continue
            for link in links:
                link["addr_info"] = [a for a in link.get("addr_info", []) if a["scope"] == scope]
            links.set([l for l in links if l["addr_info"]])
        elif strcmp(opt, "up"):
            links.set([l for l in links if "UP" in l.get("flags", [])])
        elif strcmp(opt, "label"):
            do_notimplemented(opt)
        elif strcmp(opt, "group"):
            do_notimplemented(opt)
        elif strcmp(opt, "master"):
            master = next_arg(argv)
            if not links.exist(master):
                invarg("Device does not exist", master)
            links.set([l for l in links if l.get("master") == master])
        elif strcmp(opt, "vrf"):
            vrf = next_arg(argv)
            if not links.exist(vrf):
                invarg("Not a valid VRF name", vrf)
            # if not is_vrf(vrf):
            #     invarg("Not a valid VRF name", vrf)
            # links = [l for l in links if l.get("master") == vrf]
            # FIXME: https://wiki.netunix.net/freebsd/network/vrf/
            do_notimplemented(opt)
        elif strcmp(opt, "nomaster"):
            links.set([l for l in links if l.present("master")])
        elif strcmp(opt, "type"):
            kind = next_arg(argv)
            if kind.endswith("_slave"):
                kind = kind.replace("_slave", "")
                links.set([l for l in links if l.present("info_slave_kind", kind)])
            else:
                links.set([l for l in links if l.present("info_kind", kind)])
        else:
            if strcmp(opt, "dev"):
                opt = next_arg(argv)
            elif matches(opt, "help"):
                usage()
            if dev:
                duparg2("dev", opt)
            if not links.exist(opt):
                stderr(f'Device "{opt}" does not exist.')
                exit(-1)
            dev = opt
            links.set([l for l in links if l.ifname == dev])

    return links


def ipaddr_list_or_flush(argv, flush=False):
    if flush:
        if not argv:
            stderr("Flush requires arguments.")
            exit(-1)
        if OPTION["preferred_family"] == AF_PACKET:
            stderr("Cannot flush link addresses.")
            exit(-1)

    links = get_ifconfig_links(argv)
    if OPTION["preferred_family"] in (AF_INET, AF_INET6, AF_MPLS, AF_BRIDGE):
        family = family_name(OPTION["preferred_family"])
        links.set([l for l in links if any(a["family"] == family for a in l.get("addr_info", []))])
        for link in links:
            link["addr_info"] = [a for a in link["addr_info"] if a["family"] == family]

    if flush:
        for link in links:
            for addr in link["addr_info"]:
                ifconfig.run(link["ifname"], addr["family"], addr["local"], "-alias")
    else:
        output(links)

    return EXIT_SUCCESS


def do_ipaddr(argv):
    if not argv:
        return ipaddr_list_or_flush(argv)

    cmd = argv.pop(0)
    if matches(cmd, "add", "change", "replace", "delete") or strcmp(cmd, "chg"):
        return ipaddr_modify(cmd, argv)
    elif matches(cmd, "show", "lst", "list"):
        return ipaddr_list_or_flush(argv)
    elif matches(cmd, "flush"):
        return ipaddr_list_or_flush(argv, flush=True)
    elif matches(cmd, "save"):
        return do_notimplemented()
    elif matches(cmd, "showdump"):
        return do_notimplemented()
    elif matches(cmd, "restore"):
        return do_notimplemented()
    elif matches(cmd, "help"):
        return usage()

    stderr(f'Command "{cmd}" is unknown, try "ip address help".')
    exit(-1)
