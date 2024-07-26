from iproute4mac.utils import *
from iproute4mac.ipaddress import ipaddr_list


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


# ip link show [ DEVICE | group GROUP ] [ up ] [ master DEVICE ] [ type ETYPE ] [ vrf NAME ]
# TYPE := [ bridge | bond | can | dummy | hsr | ifb | ipoib | macvlan | macvtap
#         | vcan | vxcan | veth | vlan | vxlan | ip6tnl | ipip | sit | gre
#         | gretap | erspan | ip6gre | ip6gretap | ip6erspan | vti | nlmon
#         | ipvlan | ipvtap | lowpan | geneve | bareudp | vrf | macsec
#         | netdevsim | rmnet | xfrm ]
# ETYPE := [ TYPE | bridge_slave | bond_slave ]
def iplink_list(argv, option):
    option["preferred_family"] = AF_PACKET
    return ipaddr_list(argv, option, usage)


def do_iplink(argv, option):
    if not argv:
        return iplink_list(argv, option)

    cmd = argv.pop(0)
    if matches(cmd, "add"):
        return do_notimplemented()
    elif matches(cmd, "change", "set"):
        return do_notimplemented()
    elif matches(cmd, "replace"):
        return do_notimplemented()
    elif matches(cmd, "delete"):
        return do_notimplemented()
    elif matches(cmd, "show", "lst", "list"):
        return iplink_list(argv, option)
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
