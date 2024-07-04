import subprocess
import iproute4mac.ifconfig as ifconfig

from iproute4mac.utils import *


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
def ipaddr_list(argv, option, usage=usage):
    cmd = subprocess.run(['ifconfig', '-v', '-L', '-a',],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         encoding="utf-8")
    if cmd.returncode != 0:
        print(cmd.stderr)
        exit(cmd.returncode)

    links = ifconfig.parse(cmd.stdout, option=option)
    while argv:
        opt = argv.pop(0)
        if opt == 'to':
            # to = next_arg(argv)
            # get_prefix(to, option['preferred_family'])
            do_notimplemented()
        elif opt == 'scope':
            scope = next_arg(argv)
            if (scope not in ('link', 'host', 'global', 'all')
               and not scope.isnumeric()):
                invarg('invalid "scope"', scope)
            if scope == 'all':
                continue
            do_notimplemented()
        elif opt == 'up':
            links = [link for link in links if ('flags' in link and 'UP' in link['flags'])]
        # TODO: elif get_filter(opt):
        elif opt == 'label':
            # label = next_opt(argv)
            do_notimplemented()
        elif opt == 'group':
            group = next_arg(argv)
            do_notimplemented()
            invarg('Invalid "group" value', group)
        elif opt == 'master':
            master = next_arg(argv)
            if not any(link['ifname'] == master for link in links):
                invarg('Device does not exist', master)
            links = [link for link in links if ('master' in link and link['master'] == master)]
        elif opt == 'vrf':
            vrf = next_arg(argv)
            if not any(link['ifname'] == vrf for link in links):
                invarg('Not a valid VRF name', vrf)
            # if not name_is_vrf(vrf):
            #     invarg('Not a valid VRF name', vrf)
            # links = [link for link in links if ('master' in link and link['master'] == vrf)]
            # FIXME: https://wiki.netunix.net/freebsd/network/vrf/
            do_notimplemented()
        elif opt == 'nomaster':
            links = [link for link in links if 'master' not in link]
        elif opt == 'type':
            kind = next_arg(argv)
            if kind.endswith('_slave'):
                kind = kind.replace('_slave', '')
                links = [link for link in links if recurse_in(link, ['linkinfo', 'info_slave_kind'], kind)]
            else:
                links = [link for link in links if recurse_in(link, ['linkinfo', 'info_kind'], kind)]
        else:
            if opt == 'dev':
                dev = next_arg(argv)
            elif opt == 'help':
                usage()
            links = [link for link in links if link['ifname'] == dev]
            if not links:
                stderr('Device "%s" does not exist.' % opt)
                exit(-1)

    if not option['show_details']:
        delete_keys(links, ['linkinfo'])

    if option['preferred_family'] in (AF_INET, AF_INET6, AF_MPLS, AF_BRIDGE):
        family = family_name(option['preferred_family'])
        links = [
            link for link in links if 'addr_info' in link and any(
                addr['family'] == family for addr in link['addr_info']
            )
        ]
    elif option['preferred_family'] == AF_PACKET:
        delete_keys(links, ['addr_info'])

    ifconfig.dumps(links, option)
    return EXIT_SUCCESS


def do_ipaddr(argv, option):
    if not argv:
        return ipaddr_list(argv, option)

    cmd = argv.pop(0)
    if 'add'.startswith(cmd):
        return do_notimplemented()
    elif ('change'.startswith(cmd)
          or 'chg'.startswith(cmd)):
        return do_notimplemented()
    elif 'replace'.startswith(cmd):
        return do_notimplemented()
    elif 'delete'.startswith(cmd):
        return do_notimplemented()
    elif ('show'.startswith(cmd)
          or 'lst'.startswith(cmd)
          or 'list'.startswith(cmd)):
        return ipaddr_list(argv, option)
    elif 'flush'.startswith(cmd):
        return do_notimplemented()
    elif 'save'.startswith(cmd):
        return do_notimplemented()
    elif 'showdump'.startswith(cmd):
        return do_notimplemented()
    elif 'restore'.startswith(cmd):
        return do_notimplemented()
    elif 'help'.startswith(cmd):
        return usage()

    stderr('Command "%s" is unknown, try "ip address help".' % cmd)
    exit(-1)
