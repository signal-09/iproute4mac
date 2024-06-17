import iproute4mac.ifconfig as ifconfig
from iproute4mac.utils import *


''' Options '''
option = {}


''' Commands '''
def do_ipaddr_usage():
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
          vcan | veth | vlan | vrf | vti | vxcan | vxlan | wwan |
          xfrm | virt_wifi }""")
    exit(-1)


# ip address [ show [ dev IFNAME ] [ scope SCOPE-ID ] [ master DEVICE ]
#                   [ type TYPE ] [ to PREFIX ] [ FLAG-LIST ]
#                   [ label LABEL ] [up] [ vrf NAME ] ]
# SCOPE-ID := [ host | link | global | NUMBER ]
# FLAG-LIST := [ FLAG-LIST ] FLAG
# FLAG  := [ permanent | dynamic | secondary | primary |
#            [-]tentative | [-]deprecated | [-]dadfailed | temporary |
#            CONFFLAG-LIST ]
# CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG
# CONFFLAG  := [ home | nodad | mngtmpaddr | noprefixroute | autojoin ]
# TYPE := { bareudp | bond | bond_slave | bridge | bridge_slave |
#           dummy | erspan | geneve | gre | gretap | ifb |
#           ip6erspan | ip6gre | ip6gretap | ip6tnl |
#           ipip | ipoib | ipvlan | ipvtap |
#           macsec | macvlan | macvtap |
#           netdevsim | nlmon | rmnet | sit | team | team_slave |
#           vcan | veth | vlan | vrf | vti | vxcan | vxlan | wwan |
#           xfrm }
def do_ipaddr_list(argv=[]):
    links = ifconfig.list(argv, option)
    ifconfig.dumps(links, option)
    return EXIT_SUCCESS


def do_ipaddr(argv=[], opts={}):
    global option
    option = opts

    if not argv:
        return do_ipaddr_list()

    cmd = argv.pop(0)
    if 'add'.startswith(cmd):
        return do_notimplemented()
    elif ('change'.startswith(cmd) or
          'chg'.startswith(cmd)):
        return do_notimplemented()
    elif 'replace'.startswith(cmd):
        return do_notimplemented()
    elif 'delete'.startswith(cmd):
        return do_notimplemented()
    elif ('show'.startswith(cmd) or
          'lst'.startswith(cmd) or
          'list'.startswith(cmd)):
        return do_ipaddr_list(argv)
    elif 'flush'.startswith(cmd):
        return do_notimplemented()
    elif 'save'.startswith(cmd):
        return do_notimplemented()
    elif 'showdump'.startswith(cmd):
        return do_notimplemented()
    elif 'restore'.startswith(cmd):
        return do_notimplemented()
    elif 'help'.startswith(cmd):
        return do_ipaddr_usage()

    stderr('Command "%s" is unknown, try "ip address help".' % cmd);
    exit(-1)
