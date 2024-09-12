import re
import sys

import iproute4mac.ifconfig as ifconfig
import iproute4mac.iplink_bond as bond
import iproute4mac.iplink_bridge as bridge
import iproute4mac.iplink_feth as feth
import iproute4mac.iplink_veth as veth
import iproute4mac.iplink_vlan as vlan
import iproute4mac.libc as libc
import iproute4mac.socket as socket
import iproute4mac.utils as utils

from iproute4mac import OPTION
from iproute4mac.ifconfig import LLADDR, IFNAME
from iproute4mac.ipaddress import get_links
from iproute4mac.utils import matches, strcmp, next_arg


def usage():
    utils.stderr("""\
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
          vcan | feth | vlan | vrf | vti | vxcan | vxlan | wwan |
          xfrm | virt_wifi }""")
    exit(libc.EXIT_ERROR)


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
        self._module.add(argv, links)

    def delete(self, argv, links):
        self._module.delete(argv, links)

    def set(self, argv, links):
        self._module.set(argv, links)

    def link(self, argv, links):
        self._module.link(argv, links)

    def free(self, argv, links):
        self._module.free(argv, links)

    def dump(self, argv, links):
        self._module.dump(argv, links)


def iplink_add(dev, link_type, args, links):
    link_type.add(dev, args)


def iplink_del(dev, link_type, args, links):
    if not (link := next((l for l in links if l["ifname"] == dev), None)):
        utils.stderr(f'Cannot find device "{dev}"')
        exit(libc.EXIT_FAILURE)

    if not link_type:
        if kind := link.get("linkinfo", {}).get("info_kind"):
            link_type = LinkType(kind)
    if link_type:
        link_type.delete(link, args)
    elif res := ifconfig.run(dev, "destroy"):
        utils.stdout(res, end="\n", optional=True)


def iplink_set(dev, link_type, args, links):
    if not (link := next((l for l in links if l["ifname"] == dev), None)):
        utils.stderr(f'Cannot find device "{dev}"')
        exit(libc.EXIT_FAILURE)

    res = ""
    for opt, value in args.items():
        if strcmp(opt, "state"):
            res += ifconfig.run(dev, value)
        elif strcmp(opt, "arp"):
            res += ifconfig.run(dev, value)
        elif strcmp(opt, "mtu"):
            res += ifconfig.run(dev, "mtu", value)
        elif strcmp(opt, "address"):
            res += ifconfig.run(dev, "lladdr", value)
        elif strcmp(opt, "master"):
            if master := next((l for l in links if l["ifname"] == value), None):
                if not link_type:
                    if not (kind := master.get("linkinfo", {}).get("info_kind")):
                        continue
                    link_type = LinkType(kind)
                link_type.link(link, master)
        elif strcmp(opt, "nomaster"):
            if master := next((l for l in links if l["ifname"] == link.get("master")), None):
                if not link_type:
                    if not (kind := link.get("linkinfo", {}).get("info_slave_kind")):
                        continue
                    link_type = LinkType(kind)
                link_type.free(link, master)

    if res:
        utils.stdout(res, end="\n", optional=True)

    if link_type:
        link_type.set(dev, args)


def iplink_modify(cmd, argv):
    # hide unrequested (but needed) system command from logs
    old_options = utils.options_override({"show_details": True, "verbose": -1})
    links = get_iplinks()
    utils.options_restore(old_options)

    dev = None
    link_type = None
    modifiers = {}
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "up", "down"):
            modifiers["state"] = opt
        elif strcmp(opt, "name"):
            name = next_arg(argv)
            if "name" in modifiers:
                utils.duparg("name", name)
            if not re.match(f"{IFNAME}$", name):
                utils.invarg('"name" not a valid ifname', name)
            modifiers["name"] = name
            if not dev:
                dev = name
        elif strcmp(opt, "index"):
            index = next_arg(argv)
            # if "index" in modifiers:
            #     utils.duparg("index", opt)
            try:
                assert 0 <= int(index) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "index" value', index)
            utils.do_notimplemented(opt)
        elif matches(opt, "link"):
            opt = next_arg(argv)
            if not links.exist(opt):
                utils.invarg("Device does not exist", opt)
            modifiers["link"] = opt
        elif matches(opt, "address"):
            lladdr = next_arg(argv)
            if not re.match(f"{LLADDR}$", lladdr):
                utils.stderr(f'"{lladdr}" is invalid lladdr.')
                exit(libc.EXIT_ERROR)
            modifiers["address"] = lladdr
        elif matches(opt, "broadcast") or strcmp(opt, "brd"):
            lladdr = next_arg(argv)
            if not re.match(f"{LLADDR}$", lladdr):
                utils.stderr(f'"{lladdr}" is invalid lladdr.')
                exit(libc.EXIT_ERROR)
            utils.do_notimplemented(opt)
        elif matches(opt, "txqueuelen", "txqlen") or strcmp(opt, "qlen"):
            qlen = next_arg(argv)
            utils.hint(
                f'per link queue length not supported, try "sysctl -w net.link.generic.system.sndq_maxlen={qlen}" instead.'
            )
            if "txqlen" in modifiers:
                utils.duparg("txqueuelen", qlen)
            try:
                assert 0 <= int(qlen) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "txqueuelen" value', qlen)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "mtu"):
            mtu = next_arg(argv)
            if "mtu" in modifiers:
                utils.duparg("mtu", mtu)
            try:
                assert 0 <= int(mtu) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "mtu" value', mtu)
            modifiers["mtu"] = mtu
        elif strcmp(opt, "xdpgeneric", "xdpdrv", "xdpoffload", "xdp"):
            utils.do_notimplemented(opt)
        elif strcmp(opt, "netns"):
            netns = next_arg(argv)
            try:
                assert 0 <= int(netns) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "netns" value', netns)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "multicast", "allmulticast"):
            multicast = next_arg(argv)
            if not strcmp(multicast, "on", "off"):
                utils.on_off(opt, multicast)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "promisc"):
            promisc = next_arg(argv)
            if not strcmp(promisc, "on", "off"):
                utils.on_off(opt, promisc)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "trailers"):
            trailers = next_arg(argv)
            if not strcmp(trailers, "on", "off"):
                utils.on_off(opt, trailers)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "arp"):
            arp = next_arg(argv)
            if not strcmp(arp, "on", "off"):
                utils.on_off(opt, arp)
            modifiers["arp"] = utils.on_off_switch(opt, arp)
        elif strcmp(opt, "carrier"):
            carrier = next_arg(argv)
            if not strcmp(carrier, "on", "off"):
                utils.on_off(opt, carrier)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "vf"):
            vf = next_arg(argv)
            try:
                assert 0 <= int(vf) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "vf" value', mtu)
            utils.do_notimplemented(opt)
        elif matches(opt, "master"):
            opt = next_arg(argv)
            if not links.exist(opt):
                utils.invarg("Device does not exist", opt)
            modifiers["master"] = opt
        elif strcmp(opt, "vrf"):
            vrf = next_arg(argv)
            if not links.exist(vrf):
                utils.invarg("Not a valid VRF name", vrf)
            # if not is_vrf(vrf):
            #     utils.invarg("Not a valid VRF name", vrf)
            # links = [l for l in links if l.get("master") == vrf)]
            # FIXME: https://wiki.netunix.net/freebsd/network/vrf/
            utils.do_notimplemented(opt)
        elif matches(opt, "nomaster"):
            modifiers["nomaster"] = True
        elif matches(opt, "dynamic"):
            dynamic = next_arg(argv)
            if not strcmp(dynamic, "on", "off"):
                utils.on_off(opt, dynamic)
            utils.do_notimplemented(opt)
        elif matches(opt, "type"):
            opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            try:
                link_type = LinkType(opt)
            except NotImplementedError:
                utils.invarg('"type" value is invalid', opt)
            if "name" not in modifiers:
                modifiers["name"] = opt
            elif not matches(opt, modifiers["name"]):
                utils.hint(f'arbitrary name "{modifiers["name"]}" not supported, try with "{opt}X"')
            break
        elif matches(opt, "alias"):
            utils.do_notimplemented(opt)
        elif strcmp(opt, "group"):
            group = next_arg(argv)
            try:
                assert 0 <= int(group) < 2**8
            except (ValueError, AssertionError):
                utils.invarg('Invalid "group" value', group)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "mode"):
            mode = next_arg(argv)
            if not strcmp(mode, "default", "dormant"):
                utils.invarg("Invalid link mode", mode)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "state"):
            state = next_arg(argv)
            if not strcmp(
                state, "unknown", "notpresent", "down", "lowerlayerdown", "testing", "dormant", "up"
            ):
                utils.invarg("Invalid operstate", state)
            utils.do_notimplemented(opt)
        elif matches(opt, "numtxqueues"):
            qlen = next_arg(argv)
            try:
                assert 0 <= int(qlen) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "numtxqueues" value', qlen)
            utils.hint(
                f'per link queue length not supported, try "sysctl -w net.link.generic.system.sndq_maxlen={qlen}" instead.'
            )
            utils.do_notimplemented(opt)
        elif matches(opt, "numrxqueues"):
            qlen = next_arg(argv)
            try:
                assert 0 <= int(qlen) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "numrxqueues" value', qlen)
            utils.hint(
                f'per link queue length not supported, try "sysctl -w net.link.generic.system.rcvq_maxlen={qlen}" instead.'
            )
            utils.do_notimplemented(opt)
        elif matches(opt, "addrgenmode"):
            mode = next_arg(argv)
            if not strcmp(mode, "eui64", "none", "stable_secret", "random"):
                utils.invarg("Invalid address generation mode", mode)
            utils.do_notimplemented(opt)
        elif matches(opt, "link-netns"):
            netns = next_arg(argv)
            try:
                assert 0 <= int(netns) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "link-netns" value', netns)
            utils.do_notimplemented(opt)
        elif matches(opt, "link-netnsid"):
            netns = next_arg(argv)
            try:
                assert 0 <= int(netns) < 2**16
            except (ValueError, AssertionError):
                utils.invarg('Invalid "link-netnsid" value', netns)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "protodown"):
            down = next_arg(argv)
            if not strcmp(down, "on", "off"):
                utils.on_off(opt, down)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "protodown_reason"):
            preason = next_arg(argv)
            try:
                assert 0 <= int(preason) < 2**32
            except (ValueError, AssertionError):
                utils.invarg("invalid protodown reason", preason)
            down = next_arg(argv)
            if not strcmp(down, "on", "off"):
                utils.on_off(opt, down)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "gso_max_size", "gso_max_segs", "gro_max_size"):
            max_size = next_arg(argv)
            try:
                assert 0 <= int(max_size) < 2**32
            except (ValueError, AssertionError):
                utils.invarg('Invalid "{opt}" value', max_size)
            utils.do_notimplemented(opt)
        elif strcmp(opt, "parentdev"):
            utils.do_notimplemented(opt)
        else:
            if matches(opt, "help"):
                usage()
            if strcmp(opt, "dev"):
                opt = next_arg(argv)
            if dev or opt != modifiers.get("name", opt):
                utils.duparg2("dev", opt)
            if not re.match(f"{IFNAME}$", opt):
                utils.invarg('"dev" not a valid ifname', opt)
            dev = opt

    if dev:
        modifiers["name"] = dev
    elif "name" in modifiers:
        dev = modifiers["name"]

    if link_type:
        link_type.parse(argv, modifiers)

    if not dev:
        utils.stderr('Not enough information: "dev" argument is required.')
        exit(libc.EXIT_ERROR)
    if argv:
        opt = next_arg(argv)
        if matches(opt, "help"):
            usage()
        utils.stderr(f'Garbage instead of arguments "{opt} ...". Try "ip link help".')
        exit(libc.EXIT_ERROR)

    if matches(cmd, "add"):
        if not link_type:
            utils.stderr('Not enough information: "type" argument is required')
            exit(libc.EXIT_ERROR)
        iplink_add(dev, link_type, modifiers, links)
    elif matches(cmd, "set", "change"):
        iplink_set(dev, link_type, modifiers, links)
    elif matches(cmd, "replace"):
        iplink_del(dev, link_type, modifiers, links)
        iplink_add(dev, link_type, modifiers, links)
    elif matches(cmd, "delete"):
        iplink_del(dev, link_type, modifiers, links)
    else:
        utils.do_notimplemented()

    return libc.EXIT_SUCCESS


def get_iplinks(argv=[]):
    links = get_links(argv, usage)
    for link in links:
        del link["addr_info"]
    return links


def iplink_list(argv):
    OPTION["preferred_family"] = socket._AF_PACKET
    utils.output(get_iplinks(argv))
    return libc.EXIT_SUCCESS


def do_iplink(argv):
    if not argv:
        return iplink_list(argv)

    cmd = argv.pop(0)
    if matches(cmd, "add", "set", "change", "replace", "delete"):
        return iplink_modify(cmd, argv)
    elif matches(cmd, "show", "lst", "list"):
        return iplink_list(argv)
    elif matches(cmd, "xstats"):
        return utils.do_notimplemented()
    elif matches(cmd, "afstats"):
        return utils.do_notimplemented()
    elif matches(cmd, "property"):
        return utils.do_notimplemented()
    elif matches(cmd, "help"):
        return usage()

    utils.stderr(f'Command "{cmd}" is unknown, try "ip link help".')
    exit(libc.EXIT_ERROR)
