import iproute4mac.ifconfig as ifconfig
import iproute4mac.iplink_vlan as vlan
import iproute4mac.iplink_bridge as bridge
import iproute4mac.iplink_bond as bond

from iproute4mac.utils import *
from iproute4mac.ipaddress import get_ifconfig_links


def usage():
    stderr("""\
Usage: ip link add [link DEV | parentdev NAME] [ name ] NAME
                   [ txqueuelen PACKETS ]
                   [ address LLADDR ]
                   [ broadcast LLADDR ]
                   [ mtu MTU ] [index IDX ]
                   [ numtxqueues QUEUE_COUNT ]
                   [ numrxqueues QUEUE_COUNT ]
                   [ netns { PID | NETNSNAME | NETNSFILE } ]
                   type TYPE [ ARGS ]

       ip link delete { DEVICE | dev DEVICE | group DEVGROUP } type TYPE [ ARGS ]

       ip link { set | change } { DEVICE | dev DEVICE | group DEVGROUP }
                       [ { up | down } ]
                       [ type TYPE ARGS ]
               [ arp { on | off } ]
               [ dynamic { on | off } ]
               [ multicast { on | off } ]
               [ allmulticast { on | off } ]
               [ promisc { on | off } ]
               [ trailers { on | off } ]
               [ carrier { on | off } ]
               [ txqueuelen PACKETS ]
               [ name NEWNAME ]
               [ address LLADDR ]
               [ broadcast LLADDR ]
               [ mtu MTU ]
               [ netns { PID | NETNSNAME | NETNSFILE } ]
               [ link-netns NAME | link-netnsid ID ]
               [ alias NAME ]
               [ vf NUM [ mac LLADDR ]
                        [ vlan VLANID [ qos VLAN-QOS ] [ proto VLAN-PROTO ] ]
                        [ rate TXRATE ]
                        [ max_tx_rate TXRATE ]
                        [ min_tx_rate TXRATE ]
                        [ spoofchk { on | off} ]
                        [ query_rss { on | off} ]
                        [ state { auto | enable | disable} ]
                        [ trust { on | off} ]
                        [ node_guid EUI64 ]
                        [ port_guid EUI64 ] ]
               [ { xdp | xdpgeneric | xdpdrv | xdpoffload } { off |
                         object FILE [ section NAME ] [ verbose ] |
                         pinned FILE } ]
               [ master DEVICE ][ vrf NAME ]
               [ nomaster ]
               [ addrgenmode { eui64 | none | stable_secret | random } ]
               [ protodown { on | off } ]
               [ protodown_reason PREASON { on | off } ]
               [ gso_max_size BYTES ] [ gso_ipv4_max_size BYTES ] [ gso_max_segs PACKETS ]
               [ gro_max_size BYTES ] [ gro_ipv4_max_size BYTES ]

       ip link show [ DEVICE | group GROUP ] [up] [master DEV] [vrf NAME] [type TYPE]
               [nomaster] [ novf ]

       ip link xstats type TYPE [ ARGS ]

       ip link afstats [ dev DEVICE ]
       ip link property add dev DEVICE [ altname NAME .. ]
       ip link property del dev DEVICE [ altname NAME .. ]

       ip link help [ TYPE ]

TYPE := { amt | bareudp | bond | bond_slave | bridge | bridge_slave |
          dsa | dummy | erspan | geneve | gre | gretap | gtp | hsr |
          ifb | ip6erspan | ip6gre | ip6gretap | ip6tnl |
          ipip | ipoib | ipvlan | ipvtap |
          macsec | macvlan | macvtap | netdevsim |
          netkit | nlmon | pfcp | rmnet | sit | team | team_slave |
          vcan | veth | vlan | vrf | vti | vxcan | vxlan | wwan |
          xfrm | virt_wifi }""")
    exit(-1)


class LinkType:
    __slots__ = ("_modulename", "_module", "_name")

    def __init__(self, kind):
        self._modulename = f"iproute4mac.iplink_{kind}"
        if self._modulename not in sys.modules:
            raise NotImplementedError(f'link type "{kind}" is not implemented')
        self._module = sys.modules[self._modulename]
        self._name = kind

    @property
    def name(self):
        return self._name

    def parse(self, argv, args):
        self._module.parse(argv, args)

    def add(self, argv, links):
        return self._module.add(argv, links)

    def set(self, argv, links):
        return self._module.set(argv, links)

    def link(self, argv, links):
        self._module.link(argv, links)

    def free(self, argv, links):
        self._module.free(argv, links)

    def dump(self, argv, links):
        self._module.dump(argv, links)


def iplink_add(dev, link_type, args, links):
    if res := link_type.add(dev, args):
        stdout(res, optional=True)
    iplink_set(dev, link_type, args, links)


def iplink_del(dev, link_type, args, links):
    if res := ifconfig.exec(dev, "destroy"):
        stdout(res, optional=True)


def iplink_set(dev, link_type, args, links):
    res = ""
    for opt, value in args.items():
        if strcmp(opt, "state"):
            res += ifconfig.exec(dev, value)
        elif strcmp(opt, "arp"):
            res += ifconfig.exec(dev, value)
        elif strcmp(opt, "mtu"):
            res += ifconfig.exec(dev, "mtu", value)
        elif strcmp(opt, "address"):
            res += ifconfig.exec(dev, "lladdr", value)
        elif strcmp(opt, "master"):
            if master := next((link for link in links if link["ifname"] == value), None):
                if not link_type:
                    if not (kind := master.get("linkinfo", {}).get("info_kind")):
                        continue
                    link_type = LinkType(kind)
                link_type.link(dev, value)
        elif strcmp(opt, "nomaster"):
            if slave := next((link for link in links if link["ifname"] == dev and "master" in link), None):
                if not link_type:
                    if not (kind := slave.get("linkinfo", {}).get("info_slave_kind")):
                        continue
                    link_type = LinkType(kind)
                link_type.free(dev, slave["master"])

    if link_type:
        res += link_type.set(dev, args)

    if res:
        stdout(res, optional=True)


def iplink_modify(cmd, argv):
    dev = None
    link_type = None
    links = get_iplinks(quiet=True, details=True)
    modifiers = {}
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "up", "down"):
            modifiers["state"] = opt
        elif strcmp(opt, "name"):
            name = next_arg(argv)
            if "name" in modifiers:
                duparg("name", name)
            if not re.match(f"{IFNAME}$", name):
                invarg('"name" not a valid ifname', name)
            modifiers["name"] = name
            if not dev:
                dev = name
        elif strcmp(opt, "index"):
            index = next_arg(argv)
            # if "index" in modifiers:
            #     duparg("index", opt)
            try:
                assert 0 <= int(index) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "index" value', index)
            do_notimplemented([opt])
        elif matches(opt, "link"):
            opt = next_arg(argv)
            if not any(link["ifname"] == opt for link in links):
                invarg("Device does not exist", opt)
            modifiers["link"] = opt
        elif matches(opt, "address"):
            lladdr = next_arg(argv)
            if not re.match(f"{LLADDR}$", lladdr):
                stderr(f'"{lladdr}" is invalid lladdr.')
                exit(-1)
            modifiers["address"] = lladdr
        elif matches(opt, "broadcast") or strcmp(opt, "brd"):
            lladdr = next_arg(argv)
            if not re.match(f"{LLADDR}$", lladdr):
                stderr(f'"{lladdr}" is invalid lladdr.')
                exit(-1)
            do_notimplemented([opt])
        elif matches(opt, "txqueuelen", "txqlen") or strcmp(opt, "qlen"):
            qlen = next_arg(argv)
            hint(f'per link queue length not supported, try "sysctl -w net.link.generic.system.sndq_maxlen={qlen}" instead.')
            if "txqlen" in modifiers:
                duparg("txqueuelen", qlen)
            try:
                assert 0 <= int(qlen) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "txqueuelen" value', qlen)
            do_notimplemented([opt])
        elif strcmp(opt, "mtu"):
            mtu = next_arg(argv)
            if "mtu" in modifiers:
                duparg("mtu", mtu)
            try:
                assert 0 <= int(mtu) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "mtu" value', mtu)
            modifiers["mtu"] = mtu
        elif strcmp(opt, "xdpgeneric", "xdpdrv", "xdpoffload", "xdp"):
            do_notimplemented([opt])
        elif strcmp(opt, "netns"):
            netns = next_arg(argv)
            try:
                assert 0 <= int(netns) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "netns" value', netns)
            do_notimplemented([opt])
        elif strcmp(opt, "multicast", "allmulticast"):
            multicast = next_arg(argv)
            if not strcmp(multicast, "on", "off"):
                on_off(opt, multicast)
            do_notimplemented([opt])
        elif strcmp(opt, "promisc"):
            promisc = next_arg(argv)
            if not strcmp(promisc, "on", "off"):
                on_off(opt, promisc)
            do_notimplemented([opt])
        elif strcmp(opt, "trailers"):
            trailers = next_arg(argv)
            if not strcmp(trailers, "on", "off"):
                on_off(opt, trailers)
            do_notimplemented([opt])
        elif strcmp(opt, "arp"):
            arp = next_arg(argv)
            if not strcmp(arp, "on", "off"):
                on_off(opt, arp)
            modifiers["arp"] = on_off_switch(opt, arp)
        elif strcmp(opt, "carrier"):
            carrier = next_arg(argv)
            if not strcmp(carrier, "on", "off"):
                on_off(opt, carrier)
            do_notimplemented([opt])
        elif strcmp(opt, "vf"):
            vf = next_arg(argv)
            try:
                assert 0 <= int(vf) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "vf" value', mtu)
            do_notimplemented([opt])
        elif matches(opt, "master"):
            opt = next_arg(argv)
            if not any(link["ifname"] == opt for link in links):
                invarg("Device does not exist", opt)
            modifiers["master"] = opt
        elif strcmp(opt, "vrf"):
            vrf = next_arg(argv)
            if not any(link["ifname"] == vrf for link in links):
                invarg("Not a valid VRF name", vrf)
            # if not is_vrf(vrf):
            #     invarg('Not a valid VRF name', vrf)
            # links = [link for link in links if ('master' in link and link['master'] == vrf)]
            # FIXME: https://wiki.netunix.net/freebsd/network/vrf/
            do_notimplemented([opt])
        elif matches(opt, "nomaster"):
            modifiers["nomaster"] = True
        elif matches(opt, "dynamic"):
            dynamic = next_arg(argv)
            if not strcmp(dynamic, "on", "off"):
                on_off(opt, dynamic)
            do_notimplemented([opt])
        elif matches(opt, "type"):
            opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            try:
                link_type = LinkType(opt)
            except NotImplementedError:
                invarg('"type" value is invalid', opt)
            if "name" not in modifiers:
                modifiers["name"] = opt
            break
        elif matches(opt, "alias"):
            do_notimplemented([opt])
        elif strcmp(opt, "group"):
            group = next_arg(argv)
            try:
                assert 0 <= int(group) < 2**8
            except (ValueError, AssertionError):
                invarg('Invalid "group" value', group)
            do_notimplemented([opt])
        elif strcmp(opt, "mode"):
            mode = next_arg(argv)
            if not strcmp(mode, "default", "dormant"):
                invarg("Invalid link mode", mode)
            do_notimplemented([opt])
        elif strcmp(opt, "state"):
            state = next_arg(argv)
            if not strcmp(state, "unknown", "notpresent", "down", "lowerlayerdown", "testing", "dormant", "up"):
                invarg("Invalid operstate", state)
            do_notimplemented([opt])
        elif matches(opt, "numtxqueues"):
            qlen = next_arg(argv)
            try:
                assert 0 <= int(qlen) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "numtxqueues" value', qlen)
            hint(f'per link queue length not supported, try "sysctl -w net.link.generic.system.sndq_maxlen={qlen}" instead.')
            do_notimplemented([opt])
        elif matches(opt, "numrxqueues"):
            qlen = next_arg(argv)
            try:
                assert 0 <= int(qlen) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "numrxqueues" value', qlen)
            hint(f'per link queue length not supported, try "sysctl -w net.link.generic.system.rcvq_maxlen={qlen}" instead.')
            do_notimplemented([opt])
        elif matches(opt, "addrgenmode"):
            mode = next_arg(argv)
            if not strcmp(mode, "eui64", "none", "stable_secret", "random"):
                invarg("Invalid address generation mode", mode)
            do_notimplemented([opt])
        elif matches(opt, "link-netns"):
            netns = next_arg(argv)
            try:
                assert 0 <= int(netns) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "link-netns" value', netns)
            do_notimplemented([opt])
        elif matches(opt, "link-netnsid"):
            netns = next_arg(argv)
            try:
                assert 0 <= int(netns) < 2**16
            except (ValueError, AssertionError):
                invarg('Invalid "link-netnsid" value', netns)
            do_notimplemented([opt])
        elif strcmp(opt, "protodown"):
            down = next_arg(argv)
            if not strcmp(down, "on", "off"):
                on_off(opt, down)
            do_notimplemented([opt])
        elif strcmp(opt, "protodown_reason"):
            preason = next_arg(argv)
            try:
                assert 0 <= int(preason) < 2**32
            except (ValueError, AssertionError):
                invarg("invalid protodown reason", preason)
            down = next_arg(argv)
            if not strcmp(down, "on", "off"):
                on_off(opt, down)
            do_notimplemented([opt])
        elif strcmp(opt, "gso_max_size", "gso_max_segs", "gro_max_size"):
            max_size = next_arg(argv)
            try:
                assert 0 <= int(max_size) < 2**32
            except (ValueError, AssertionError):
                invarg('Invalid "{opt}" value', max_size)
            do_notimplemented([opt])
        elif strcmp(opt, "parentdev"):
            do_notimplemented([opt])
        else:
            if matches(opt, "help"):
                usage()
            if strcmp(opt, "dev"):
                opt = next_arg(argv)
            if dev or opt != modifiers.get("name", opt):
                duparg2("dev", opt)
            if not re.match(f"{IFNAME}$", opt):
                invarg('"dev" not a valid ifname', opt)
            dev = opt

    if dev:
        modifiers["name"] = dev
    elif "name" in modifiers:
        dev = modifiers["name"]

    if link_type:
        link_type.parse(argv, modifiers)

    if not dev:
        stderr('Not enough information: "dev" argument is required.')
        exit(-1)
    if argv:
        opt = next_arg(argv)
        if matches(opt, "help"):
            usage()
        stderr(f'Garbage instead of arguments "{opt} ...". Try "ip link help".')
        exit(-1)

    if matches(cmd, "add"):
        if not link_type:
            stderr('Not enough information: "type" argument is required')
            exit(-1)
        iplink_add(dev, link_type, modifiers, links)
    elif matches(cmd, "set", "change"):
        iplink_set(dev, link_type, modifiers, links)
    elif matches(cmd, "replace"):
        iplink_del(dev, link_type, modifiers, links)
        iplink_add(dev, link_type, modifiers, links)
    elif matches(cmd, "delete"):
        iplink_del(dev, link_type, modifiers, links)
    else:
        do_notimplemented()

    return EXIT_SUCCESS


def get_iplinks(argv=[], quiet=False, details=False):
    if quiet != OPTION["quiet"]:
        OPTION["quiet"] = quiet
        quiet = not quiet
    if details != OPTION["show_details"]:
        OPTION["show_details"] = details
        details = not details
    links = get_ifconfig_links(argv, usage)
    if quiet != OPTION["quiet"]:
        OPTION["quiet"] = quiet
    if details != OPTION["show_details"]:
        OPTION["show_details"] = details
    delete_keys(links, "addr_info")
    return links


def iplink_list(argv):
    ifconfig.dumps(get_iplinks(argv))
    return EXIT_SUCCESS


def do_iplink(argv):
    if not argv:
        return iplink_list(argv)

    cmd = argv.pop(0)
    if matches(cmd, "add", "set", "change", "replace", "delete"):
        return iplink_modify(cmd, argv)
    elif matches(cmd, "show", "lst", "list"):
        return iplink_list(argv)
    elif matches(cmd, "xstats"):
        return do_notimplemented()
    elif matches(cmd, "afstats"):
        return do_notimplemented()
    elif matches(cmd, "property"):
        return do_notimplemented()
    elif matches(cmd, "help"):
        return usage()

    stderr(f'Command "{cmd}" is unknown, try "ip link help".')
    exit(-1)
