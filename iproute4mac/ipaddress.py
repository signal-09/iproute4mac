import iproute4mac.ifconfig as ifconfig
import iproute4mac.libc as libc
import iproute4mac.prefix as prefix
import iproute4mac.socket as socket
import iproute4mac.utils as utils

from iproute4mac import OPTION
from iproute4mac.prefix import Prefix
from iproute4mac.utils import matches, strcmp, next_arg, get_addr, get_prefix


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
    utils.stderr("""\
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
    exit(libc.EXIT_ERROR)


def ipaddr_add(dev, local, broadcast):
    args = ()
    if local:
        address = str(local)
        proto = "inet" if local.version == 4 else "inet6"
    else:
        address = None
        proto = None
    if broadcast:
        if not local or local.family != socket._AF_INET:
            utils.stderr("Broadcast can be set only for IPv4 addresses")
            exit(libc.EXIT_FAILURE)
        if broadcast == "+":
            broadcast = str(local._network.broadcast_address)
        elif broadcast == "-":
            broadcast = str(local._network.network_address)
        else:
            broadcast = str(broadcast)
        args += ("broadcast", broadcast)

    if res := ifconfig.run(dev, proto, address, args, "alias"):
        utils.stdout(res, end="\n", optional=True)


def ipaddr_del(dev, local):
    if local:
        address = str(local)
        proto = "inet" if local.version == 4 else "inet6"
    else:
        address = None
        proto = None

    if res := ifconfig.run(dev, proto, address, "-alias"):
        utils.stdout(res, end="\n", optional=True)


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
                utils.duparg("peer", opt)
            peer = get_prefix(opt, OPTION["preferred_family"])
            OPTION["preferred_family"] = peer.family
        elif matches(opt, "broadcast") or strcmp(opt, "brd"):
            opt = next_arg(argv)
            if broadcast:
                utils.duparg("broadcast", opt)
            if strcmp(opt, "+", "-"):
                broadcast = opt
            else:
                broadcast = get_addr(opt, OPTION["preferred_family"])
                OPTION["preferred_family"] = broadcast.family
        elif strcmp(opt, "anycast"):
            opt = next_arg(argv)
            if anycast:
                utils.duparg("anycast", opt)
            anycast = get_addr(opt, OPTION["preferred_family"])
            # FIXME: anycast is supported by ifconfig
            utils.do_notimplemented(opt)
        elif strcmp(opt, "scope"):
            utils.do_notimplemented(opt)
        elif strcmp(opt, "dev"):
            dev = next_arg(argv)
        elif strcmp(opt, "label"):
            utils.do_notimplemented(opt)
        elif matches(opt, "metric", "priority", "preference"):
            metric = next_arg(argv)
            try:
                assert 0 <= int(metric) < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"metric" value is invalid', metric)
            utils.do_notimplemented(opt)
        elif matches(opt, "valid_lft"):
            lft = next_arg(argv)
            utils.hint(f'try "sysctl -w net.inet6.ip6.tempvltime={lft}" instead.')
            utils.do_notimplemented(opt)
        elif matches(opt, "preferred_lft"):
            lft = next_arg(argv)
            utils.hint(f'try "sysctl -w net.inet6.ip6.temppltime={lft}" instead.')
            utils.do_notimplemented(opt)
        elif strcmp(opt, FLAG_MASK):
            utils.do_notimplemented(opt)
        else:
            if strcmp(opt, "local"):
                opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            if local:
                utils.duparg2("local", opt)
            local = get_prefix(opt, OPTION["preferred_family"])
            if "/" not in opt:
                local = Prefix(f"{opt}/{local.max_prefixlen}")
            OPTION["preferred_family"] = local.family

    if not dev:
        utils.stderr('Not enough information: "dev" argument is required.')
        return libc.EXIT_FAILURE

    if matches(cmd, "add", "change", "replace") or strcmp(cmd, "chg"):
        ipaddr_add(dev, local, broadcast)
    elif matches(cmd, "delete"):
        ipaddr_del(dev, local)
    else:
        utils.do_notimplemented()

    return libc.EXIT_SUCCESS


def get_ifconfig_links():
    return ifconfig.IpAddress()


def get_links(argv, usage=usage):
    links = get_ifconfig_links()
    dev = None
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "to"):
            to = get_prefix(next_arg(argv), OPTION["preferred_family"])
            if to.family != socket._AF_UNSPEC:
                OPTION["preferred_family"] = to.family
            for link in links:
                link["addr_info"] = [a for a in link.get("addr_info", []) if a["local"] in to]
            links.set([l for l in links if l["addr_info"]])
        elif strcmp(opt, "scope"):
            scope = next_arg(argv)
            if scope not in ("link", "host", "global", "all") and not scope.isdigit():
                utils.invarg('invalid "scope"', scope)
            if scope == "all":
                continue
            for link in links:
                link["addr_info"] = [a for a in link.get("addr_info", []) if a["scope"] == scope]
            links.set([l for l in links if l["addr_info"]])
        elif strcmp(opt, "up"):
            links.set([l for l in links if "UP" in l.get("flags", [])])
        elif strcmp(opt, "label"):
            utils.do_notimplemented(opt)
        elif strcmp(opt, "group"):
            utils.do_notimplemented(opt)
        elif strcmp(opt, "master"):
            master = next_arg(argv)
            if not links.exist(master):
                utils.invarg("Device does not exist", master)
            links.set([l for l in links if l.get("master") == master])
        elif strcmp(opt, "vrf"):
            vrf = next_arg(argv)
            if not links.exist(vrf):
                utils.invarg("Not a valid VRF name", vrf)
            # if not is_vrf(vrf):
            #     utils.invarg("Not a valid VRF name", vrf)
            # links = [l for l in links if l.get("master") == vrf]
            # FIXME: https://wiki.netunix.net/freebsd/network/vrf/
            utils.do_notimplemented(opt)
        elif strcmp(opt, "nomaster"):
            links.set([l for l in links if l.present("master")])
        elif strcmp(opt, "type"):
            kind = next_arg(argv)
            if kind.endswith("_slave"):
                kind = kind.replace("_slave", "")
                links.set([l for l in links if l.present("info_slave_kind", kind, recurse=True)])
            else:
                links.set([l for l in links if l.present("info_kind", kind, recurse=True)])
        else:
            if strcmp(opt, "dev"):
                opt = next_arg(argv)
            elif matches(opt, "help"):
                usage()
            if dev:
                utils.duparg2("dev", opt)
            if not links.exist(opt):
                utils.stderr(f'Device "{opt}" does not exist.')
                exit(libc.EXIT_ERROR)
            dev = opt
            links.set([i for i in links if i.name == dev])

    return links


def ipaddr_list_or_flush(argv, flush=False):
    if flush:
        if not argv:
            utils.stderr("Flush requires arguments.")
            exit(libc.EXIT_ERROR)
        if OPTION["preferred_family"] == socket._AF_PACKET:
            utils.stderr("Cannot flush link addresses.")
            exit(libc.EXIT_ERROR)

    links = get_links(argv)
    if OPTION["preferred_family"] in (
        socket._AF_INET,
        socket._AF_INET6,
        socket._AF_MPLS,
        socket._AF_BRIDGE,
    ):
        family = socket.family_name(OPTION["preferred_family"])
        for interface in links:
            interface["addr_info"] = [
                addr for addr in interface["addr_info"] if addr["family"] == family
            ]
        links.set([i for i in links if i.present("addr_info", strict=True)])

    if flush:
        for interface in links.list():
            for addr in interface["addr_info"]:
                ifconfig.run(interface.name, addr["family"], addr["local"], "-alias")
    else:
        utils.output(links)

    return libc.EXIT_SUCCESS


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
        return utils.do_notimplemented()
    elif matches(cmd, "showdump"):
        return utils.do_notimplemented()
    elif matches(cmd, "restore"):
        return utils.do_notimplemented()
    elif matches(cmd, "help"):
        return usage()

    utils.stderr(f'Command "{cmd}" is unknown, try "ip address help".')
    exit(libc.EXIT_ERROR)
