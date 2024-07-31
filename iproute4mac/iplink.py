import iproute4mac.ifconfig as ifconfig

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


# ip route { add | del | change | append | replace } ROUTE
# ROUTE := NODE_SPEC [ INFO_SPEC ]
# NODE_SPEC := [ TYPE ] PREFIX [ tos TOS ]
#              [ table TABLE_ID ] [ proto RTPROTO ]
#              [ scope SCOPE ] [ metric METRIC ]
#              [ ttl-propagate { enabled | disabled } ]
# INFO_SPEC := { NH | nhid ID } OPTIONS FLAGS [ nexthop NH ]...
# NH := [ encap ENCAPTYPE ENCAPHDR ] [ via [ FAMILY ] ADDRESS ]
#       [ dev STRING ] [ weight NUMBER ] NHFLAGS
# FAMILY := [ inet | inet6 | mpls | bridge | link ]
# OPTIONS := FLAGS [ mtu NUMBER ] [ advmss NUMBER ] [ as [ to ] ADDRESS ]
#            [ rtt TIME ] [ rttvar TIME ] [ reordering NUMBER ]
#            [ window NUMBER ] [ cwnd NUMBER ] [ initcwnd NUMBER ]
#            [ ssthresh NUMBER ] [ realms REALM ] [ src ADDRESS ]
#            [ rto_min TIME ] [ hoplimit NUMBER ] [ initrwnd NUMBER ]
#            [ features FEATURES ] [ quickack BOOL ] [ congctl NAME ]
#            [ pref PREF ] [ expires TIME ] [ fastopen_no_cookie BOOL ]
# TYPE := { unicast | local | broadcast | multicast | throw |
#           unreachable | prohibit | blackhole | nat }
# TABLE_ID := [ local | main | default | all | NUMBER ]
# SCOPE := [ host | link | global | NUMBER ]
# NHFLAGS := [ onlink | pervasive ]
# RTPROTO := [ kernel | boot | static | NUMBER ]
# PREF := [ low | medium | high ]
# TIME := NUMBER[s|ms]
# BOOL := [1|0]
# FEATURES := ecn
# ENCAPTYPE := [ mpls | ip | ip6 | seg6 | seg6local | rpl | ioam6 ]
# ENCAPHDR := [ MPLSLABEL | SEG6HDR | SEG6LOCAL | IOAM6HDR ]
# SEG6HDR := [ mode SEGMODE ] segs ADDR1,ADDRi,ADDRn [hmac HMACKEYID] [cleanup]
# SEGMODE := [ encap | inline ]
# SEG6LOCAL := action ACTION [ OPTIONS ] [ count ]
# ACTION := { End | End.X | End.T | End.DX2 | End.DX6 | End.DX4 |
#             End.DT6 | End.DT4 | End.DT46 | End.B6 | End.B6.Encaps |
#             End.BM | End.S | End.AS | End.AM | End.BPF }
# OPTIONS := OPTION [ OPTIONS ]
# OPTION := { srh SEG6HDR | nh4 ADDR | nh6 ADDR | iif DEV | oif DEV |
#             table TABLEID | vrftable TABLEID | endpoint PROGNAME }
# IOAM6HDR := trace prealloc type IOAM
def iplink_modify(argv):
    name = None
    dev = None
    while argv:
        opt = argv.pop(0)
        #        if strcmp(opt, "up"):
        #            req->i.ifi_change |= IFF_UP
        #            req->i.ifi_flags |= IFF_UP
        #        elif strcmp(opt, "down"):
        #            req->i.ifi_change |= IFF_UP
        #            req->i.ifi_flags &= ~IFF_UP
        if strcmp(opt, "name"):
            opt = next_arg(argv)
            if name:
                duparg("name", opt)
            if not re.match(f"{IFNAME}$", opt):
                invarg('"name" not a valid ifname', opt)
            name = opt
            if not dev:
                dev = name
        #        elif strcmp(opt, "index"):
        #            opt = next_arg(argv)
        #            if (index)
        #                duparg("index", *argv)
        #            index = atoi(*argv)
        #            if (index <= 0)
        #                invarg("Invalid \"index\" value", *argv)
        elif matches(opt, "link"):
            link = next_arg(argv)
            do_notimplemented([link])
        #        elif matches(opt, "address"):
        #            opt = next_arg(argv)
        #            addr_len = ll_addr_a2n(abuf, sizeof(abuf), *argv)
        #            if (addr_len < 0)
        #                return -1
        #            addattr_l(&req->n, sizeof(*req),
        #                  IFLA_ADDRESS, abuf, addr_len)
        #        elif matches(opt, "broadcast") or strcmp(opt, "brd"):
        #            opt = next_arg(argv)
        #            len = ll_addr_a2n(abuf, sizeof(abuf), *argv)
        #            if (len < 0)
        #                return -1
        #            addattr_l(&req->n, sizeof(*req),
        #                  IFLA_BROADCAST, abuf, len)
        #        elif matches(opt, "txqueuelen", "txqlen") or strcmp(opt, "qlen"):
        #            opt = next_arg(argv)
        #            if (qlen != -1)
        #                duparg("txqueuelen", *argv)
        #            if (get_integer(&qlen,  *argv, 0))
        #                invarg("Invalid \"txqueuelen\" value\n", *argv)
        #            addattr_l(&req->n, sizeof(*req),
        #                  IFLA_TXQLEN, &qlen, 4)
        #        elif strcmp(opt, "mtu"):
        #            opt = next_arg(argv)
        #            if (mtu != -1)
        #                duparg("mtu", *argv)
        #            if (get_integer(&mtu, *argv, 0))
        #                invarg("Invalid \"mtu\" value\n", *argv)
        #            addattr_l(&req->n, sizeof(*req), IFLA_MTU, &mtu, 4)
        #        elif strcmp(opt, "xdpgeneric", "xdpdrv", "xdpoffload", "xdp"):
        #            bool generic = strcmp(opt, "xdpgeneric") == 0
        #            bool drv = strcmp(opt, "xdpdrv") == 0
        #            bool offload = strcmp(opt, "xdpoffload") == 0
        #
        #            opt = next_arg(argv)
        #            if (xdp_parse(&argc, &argv, req, dev,
        #                      generic, drv, offload))
        #                exit(-1)
        #
        #            if (offload && name == dev)
        #                dev = NULL
        #        elif strcmp(opt, "netns"):
        #            opt = next_arg(argv)
        #            if (netns != -1)
        #                duparg("netns", *argv)
        #            netns = netns_get_fd(*argv)
        #            if (netns >= 0)
        #                addattr_l(&req->n, sizeof(*req), IFLA_NET_NS_FD,
        #                      &netns, 4)
        #            else if (get_integer(&netns, *argv, 0):
        #                addattr_l(&req->n, sizeof(*req),
        #                      IFLA_NET_NS_PID, &netns, 4)
        #            else
        #                invarg("Invalid \"netns\" value\n", *argv)
        #            move_netns = true
        #        elif strcmp(opt, "multicast"):
        #            opt = next_arg(argv)
        #            req->i.ifi_change |= IFF_MULTICAST
        #
        #            if strcmp(opt, "on"):
        #                req->i.ifi_flags |= IFF_MULTICAST
        #            else if strcmp(opt, "off"):
        #                req->i.ifi_flags &= ~IFF_MULTICAST
        #            else
        #                return on_off("multicast", *argv)
        #        elif strcmp(opt, "allmulticast"):
        #            opt = next_arg(argv)
        #            req->i.ifi_change |= IFF_ALLMULTI
        #
        #            if strcmp(opt, "on"):
        #                req->i.ifi_flags |= IFF_ALLMULTI
        #            else if strcmp(opt, "off"):
        #                req->i.ifi_flags &= ~IFF_ALLMULTI
        #            else
        #                return on_off("allmulticast", *argv)
        #        elif strcmp(opt, "promisc"):
        #            opt = next_arg(argv)
        #            req->i.ifi_change |= IFF_PROMISC
        #
        #            if strcmp(opt, "on"):
        #                req->i.ifi_flags |= IFF_PROMISC
        #            else if strcmp(opt, "off"):
        #                req->i.ifi_flags &= ~IFF_PROMISC
        #            else
        #                return on_off("promisc", *argv)
        #        elif strcmp(opt, "trailers"):
        #            opt = next_arg(argv)
        #            req->i.ifi_change |= IFF_NOTRAILERS
        #
        #            if strcmp(opt, "off"):
        #                req->i.ifi_flags |= IFF_NOTRAILERS
        #            else if strcmp(opt, "on"):
        #                req->i.ifi_flags &= ~IFF_NOTRAILERS
        #            else
        #                return on_off("trailers", *argv)
        #        elif strcmp(opt, "arp"):
        #            opt = next_arg(argv)
        #            req->i.ifi_change |= IFF_NOARP
        #
        #            if strcmp(opt, "on"):
        #                req->i.ifi_flags &= ~IFF_NOARP
        #            else if strcmp(opt, "off"):
        #                req->i.ifi_flags |= IFF_NOARP
        #            else
        #                return on_off("arp", *argv)
        #        elif strcmp(opt, "carrier"):
        #            int carrier
        #
        #            opt = next_arg(argv)
        #            carrier = parse_on_off("carrier", *argv, &err)
        #            if (err)
        #                return err
        #
        #            addattr8(&req->n, sizeof(*req), IFLA_CARRIER, carrier)
        #        elif strcmp(opt, "vf"):
        #            struct rtattr *vflist
        #
        #            opt = next_arg(argv)
        #            if (get_integer(&vf,  *argv, 0))
        #                invarg("Invalid \"vf\" value\n", *argv)
        #
        #            vflist = addattr_nest(&req->n, sizeof(*req),
        #                          IFLA_VFINFO_LIST)
        #            if (!dev)
        #                missarg("dev")
        #
        #            len = iplink_parse_vf(vf, &argc, &argv, req, dev)
        #            if (len < 0)
        #                return -1
        #            addattr_nest_end(&req->n, vflist)
        #
        #            if (name == dev)
        #                dev = NULL
        #        elif matches(opt, "master"):
        #            int ifindex
        #
        #            opt = next_arg(argv)
        #            ifindex = ll_name_to_index(*argv)
        #            if (!ifindex)
        #                invarg("Device does not exist\n", *argv)
        #            addattr_l(&req->n, sizeof(*req), IFLA_MASTER,
        #                  &ifindex, 4)
        #        elif strcmp(opt, "vrf"):
        #            int ifindex
        #
        #            opt = next_arg(argv)
        #            ifindex = ll_name_to_index(*argv)
        #            if (!ifindex)
        #                invarg("Not a valid VRF name\n", *argv)
        #            if (!name_is_vrf(*argv))
        #                invarg("Not a valid VRF name\n", *argv)
        #            addattr_l(&req->n, sizeof(*req), IFLA_MASTER,
        #                  &ifindex, sizeof(ifindex))
        #        elif matches(opt, "nomaster"):
        #            int ifindex = 0
        #
        #            addattr_l(&req->n, sizeof(*req), IFLA_MASTER,
        #                  &ifindex, 4)
        #        elif matches(opt, "dynamic"):
        #            opt = next_arg(argv)
        #            req->i.ifi_change |= IFF_DYNAMIC
        #
        #            if strcmp(opt, "on"):
        #                req->i.ifi_flags |= IFF_DYNAMIC
        #            else if strcmp(opt, "off"):
        #                req->i.ifi_flags &= ~IFF_DYNAMIC
        #            else
        #                return on_off("dynamic", *argv)
        #        elif matches(opt, "type"):
        #            opt = next_arg(argv)
        #            *type = *argv
        #            argc--; argv++
        #            break
        #        elif matches(opt, "alias"):
        #            opt = next_arg(argv)
        #            len = strlen(*argv)
        #            if (len >= IFALIASZ)
        #                invarg("alias too long\n", *argv)
        #            addattr_l(&req->n, sizeof(*req), IFLA_IFALIAS,
        #                  *argv, len)
        #        elif strcmp(opt, "group"):
        #            opt = next_arg(argv)
        #            if (group != -1)
        #                duparg("group", *argv)
        #            if (rtnl_group_a2n(&group, *argv))
        #                invarg("Invalid \"group\" value\n", *argv)
        #            addattr32(&req->n, sizeof(*req), IFLA_GROUP, group)
        #        elif strcmp(opt, "mode"):
        #            int mode
        #
        #            opt = next_arg(argv)
        #            mode = get_link_mode(*argv)
        #            if (mode < 0)
        #                invarg("Invalid link mode\n", *argv)
        #            addattr8(&req->n, sizeof(*req), IFLA_LINKMODE, mode)
        #        elif strcmp(opt, "state"):
        #            int state
        #
        #            opt = next_arg(argv)
        #            state = get_operstate(*argv)
        #            if (state < 0)
        #                invarg("Invalid operstate\n", *argv)
        #
        #            addattr8(&req->n, sizeof(*req), IFLA_OPERSTATE, state)
        #        elif matches(opt, "numtxqueues"):
        #            opt = next_arg(argv)
        #            if (numtxqueues != -1)
        #                duparg("numtxqueues", *argv)
        #            if (get_integer(&numtxqueues, *argv, 0))
        #                invarg("Invalid \"numtxqueues\" value\n",
        #                       *argv)
        #            addattr_l(&req->n, sizeof(*req), IFLA_NUM_TX_QUEUES,
        #                  &numtxqueues, 4)
        #        elif matches(opt, "numrxqueues"):
        #            opt = next_arg(argv)
        #            if (numrxqueues != -1)
        #                duparg("numrxqueues", *argv)
        #            if (get_integer(&numrxqueues, *argv, 0))
        #                invarg("Invalid \"numrxqueues\" value\n",
        #                       *argv)
        #            addattr_l(&req->n, sizeof(*req), IFLA_NUM_RX_QUEUES,
        #                  &numrxqueues, 4)
        #        elif matches(opt, "addrgenmode"):
        #            struct rtattr *afs, *afs6
        #            int mode
        #
        #            opt = next_arg(argv)
        #            mode = get_addr_gen_mode(*argv)
        #            if (mode < 0)
        #                invarg("Invalid address generation mode\n",
        #                       *argv)
        #            afs = addattr_nest(&req->n, sizeof(*req), IFLA_AF_SPEC)
        #            afs6 = addattr_nest(&req->n, sizeof(*req), AF_INET6)
        #            addattr8(&req->n, sizeof(*req),
        #                 IFLA_INET6_ADDR_GEN_MODE, mode)
        #            addattr_nest_end(&req->n, afs6)
        #            addattr_nest_end(&req->n, afs)
        #        elif matches(opt, "link-netns"):
        #            opt = next_arg(argv)
        #            if (link_netnsid != -1)
        #                duparg("link-netns/link-netnsid", *argv)
        #            link_netnsid = get_netnsid_from_name(*argv)
        #            /* No nsid? Try to assign one. */
        #            if (link_netnsid < 0)
        #                set_netnsid_from_name(*argv, -1)
        #            link_netnsid = get_netnsid_from_name(*argv)
        #            if (link_netnsid < 0)
        #                invarg("Invalid \"link-netns\" value\n",
        #                       *argv)
        #            addattr32(&req->n, sizeof(*req), IFLA_LINK_NETNSID,
        #                  link_netnsid)
        #        elif matches(opt, "link-netnsid"):
        #            opt = next_arg(argv)
        #            if (link_netnsid != -1)
        #                duparg("link-netns/link-netnsid", *argv)
        #            if (get_integer(&link_netnsid, *argv, 0))
        #                invarg("Invalid \"link-netnsid\" value\n",
        #                       *argv)
        #            addattr32(&req->n, sizeof(*req), IFLA_LINK_NETNSID,
        #                  link_netnsid)
        #        elif strcmp(opt, "protodown"):
        #            unsigned int proto_down
        #
        #            opt = next_arg(argv)
        #            proto_down = parse_on_off("protodown", *argv, &err)
        #            if (err)
        #                return err
        #            addattr8(&req->n, sizeof(*req), IFLA_PROTO_DOWN,
        #                 proto_down)
        #        elif strcmp(opt, "protodown_reason"):
        #            struct rtattr *pr
        #            __u32 preason = 0, prvalue = 0, prmask = 0
        #
        #            opt = next_arg(argv)
        #            if (protodown_reason_a2n(&preason, *argv))
        #                invarg("invalid protodown reason\n", *argv)
        #            opt = next_arg(argv)
        #            prmask = 1 << preason
        #            if matches(opt, "on"):
        #                prvalue |= prmask
        #            else if matches(opt, "off"):
        #                prvalue &= ~prmask
        #            else
        #                return on_off("protodown_reason", *argv)
        #            pr = addattr_nest(&req->n, sizeof(*req),
        #                      IFLA_PROTO_DOWN_REASON | NLA_F_NESTED)
        #            addattr32(&req->n, sizeof(*req),
        #                  IFLA_PROTO_DOWN_REASON_MASK, prmask)
        #            addattr32(&req->n, sizeof(*req),
        #                  IFLA_PROTO_DOWN_REASON_VALUE, prvalue)
        #            addattr_nest_end(&req->n, pr)
        #        elif strcmp(opt, "gso_max_size"):
        #            unsigned int max_size
        #
        #            opt = next_arg(argv)
        #            if (get_unsigned(&max_size, *argv, 0))
        #                invarg("Invalid \"gso_max_size\" value\n",
        #                       *argv)
        #            addattr32(&req->n, sizeof(*req),
        #                  IFLA_GSO_MAX_SIZE, max_size)
        #        elif strcmp(opt, "gso_max_segs"):
        #            unsigned int max_segs
        #
        #            opt = next_arg(argv)
        #            if (get_unsigned(&max_segs, *argv, 0) ||
        #                max_segs > GSO_MAX_SEGS)
        #                invarg("Invalid \"gso_max_segs\" value\n",
        #                       *argv)
        #            addattr32(&req->n, sizeof(*req),
        #                  IFLA_GSO_MAX_SEGS, max_segs)
        #        elif strcmp(opt, "gro_max_size"):
        #            unsigned int max_size
        #
        #            opt = next_arg(argv)
        #            if (get_unsigned(&max_size, *argv, 0))
        #                invarg("Invalid \"gro_max_size\" value\n",
        #                       *argv)
        #            addattr32(&req->n, sizeof(*req),
        #                  IFLA_GRO_MAX_SIZE, max_size)
        #        elif strcmp(opt, "parentdev"):
        #            opt = next_arg(argv)
        #            addattr_l(&req->n, sizeof(*req), IFLA_PARENT_DEV_NAME,
        #                  *argv, strlen(*argv) + 1)
        else:
            if matches(opt, "help"):
                usage()

            if strcmp(opt, "dev"):
                opt = next_arg(argv)
            if dev != name:
                duparg2("dev", opt)
            if not re.match(f"{IFNAME}$", opt):
                invarg('"dev" not a valid ifname', opt)
            dev = opt

    # Allow "ip link add dev" and "ip link add name"
    if not name:
        name = dev
    elif not dev:
        dev = name
    elif name != dev:
        name = dev

    return EXIT_SUCCESS


# ip link show [ DEVICE | group GROUP ] [ up ] [ master DEVICE ] [ type ETYPE ] [ vrf NAME ]
# TYPE := [ bridge | bond | can | dummy | hsr | ifb | ipoib | macvlan | macvtap
#         | vcan | vxcan | veth | vlan | vxlan | ip6tnl | ipip | sit | gre
#         | gretap | erspan | ip6gre | ip6gretap | ip6erspan | vti | nlmon
#         | ipvlan | ipvtap | lowpan | geneve | bareudp | vrf | macsec
#         | netdevsim | rmnet | xfrm ]
# ETYPE := [ TYPE | bridge_slave | bond_slave ]
def iplink_list(argv):
    links = get_ifconfig_links(argv, usage)
    delete_keys(links, "addr_info")
    ifconfig.dumps(links)

    return EXIT_SUCCESS


def do_iplink(argv):
    if not argv:
        return iplink_list(argv)

    cmd = argv.pop(0)
    if matches(cmd, "add", "set", "change", "replace", "delete"):
        return iplink_modify(argv)
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
