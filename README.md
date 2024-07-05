# iproute4mac

[![GH Actions CI](https://github.com/signal-09/iproute4mac/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/signal-09/iproute4mac/actions/workflows/python-package.yml)

This is a macOS network wrapper to imitate GNU/Linux [iproute2](https://wiki.linuxfoundation.org/networking/iproute2) suite, inspired by the [iproute2mac](https://github.com/brona/iproute2mac) project.

> **WARNING:** early Aplha stage
>
> Read only `ip link [show]`, `ip address [show]`, and `ip route [show]` objects implemented for now.

## Installation

In order to use this tap, you need to install [Homebrew](https://brew.sh).

Then, to run a default installation, run:

```shell
brew install signal-09/repo/iproute4mac
```

### Installing latest Git version (`HEAD`)

You can install the latest Git version by adding the `--HEAD` option:

```shell
brew install signal-09/repo/iproute4mac --HEAD
```

## Usage

**iproute4mac** try to imitate as much as possible the *look & feel* of the GNU/Linux iproute2 suite, but macOS (Darwin) is a BSD derivative, and some aspects cannot be replicated at all.

### `ip address show`: look at protocol addresses

> Syntax:
>
> ```
ip address [ show [ dev IFNAME ] [ scope SCOPE-ID ] [ master DEVICE ]
                  [ type TYPE ] [ to PREFIX ] [ FLAG-LIST ]
                  [ label LABEL ] [up] [ vrf NAME ] ]
SCOPE-ID := [ host | link | global | NUMBER ]
FLAG-LIST := [ FLAG-LIST ] FLAG
FLAG  := [ permanent | dynamic | secondary | primary |
           [-]tentative | [-]deprecated | [-]dadfailed | temporary |
           CONFFLAG-LIST ]
CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG
CONFFLAG  := [ home | nodad | mngtmpaddr | noprefixroute | autojoin ]
TYPE := { bareudp | bond | bond_slave | bridge | bridge_slave |
          dummy | erspan | geneve | gre | gretap | ifb |
          ip6erspan | ip6gre | ip6gretap | ip6tnl |
          ipip | ipoib | ipvlan | ipvtap |
          macsec | macvlan | macvtap |
          netdevsim | nlmon | rmnet | sit | team | team_slave |
          vcan | veth | vlan | vrf | vti | vxcan | vxlan | wwan |
          xfrm }
```

Shows IPv4 and IPv6 addresses assigned to all network interfaces. The 'show' subcommand can be omitted:

```shell
ip address show
```

Same as above except that only IPv6 addresses assigned to active network interfaces are shown:

```shell
ip -6 address show up
```

Shows IPv4 and IPv6 addresses assigned to network interface en0 in pretty printed JSON:

```shell
ip -j -p address show dev en0
```

Shows IPv4 only addresses assigned to networks member of bridge0:

```shell
ip -4 address show master bridge0
```

#### Notes

1. `qdisc` (queuing discipline) is part of the Linux Traffic Control subsystem (TC) via the `tc` utility. Even if this information is not reported, similar results in traffic control and shaping can be achieved using `dnctl` and `pfctl`.
2. `address lifetime` for IPv6 addresses (-L flag of `ifconfig`) is not provided anymore in Sonoma (macOS 14); for IPv4, addresses *valid* and *prederred* lifetime, is supposed *forever* (0xffffffff = 4.294.967.295 = 32 bit).

### `ip link show`: display device attributes

> Syntax:
>
> ```
ip link show [ DEVICE | group GROUP ] [ up ] [ master DEVICE ] [ type ETYPE ] [ vrf NAME ]
TYPE := [ bridge | bond | can | dummy | hsr | ifb | ipoib | macvlan | macvtap
        | vcan | vxcan | veth | vlan | vxlan | ip6tnl | ipip | sit | gre
        | gretap | erspan | ip6gre | ip6gretap | ip6erspan | vti | nlmon
        | ipvlan | ipvtap | lowpan | geneve | bareudp | vrf | macsec
        | netdevsim | rmnet | xfrm ]
ETYPE := [ TYPE | bridge_slave | bond_slave ]
```

### `ip route show`: list routes

> Syntax:
>
>```
ip route [ list [ SELECTOR ] ]
SELECTOR := [ root PREFIX ] [ match PREFIX ] [ exact PREFIX ]
            [ table TABLE_ID ] [ vrf NAME ] [ proto RTPROTO ]
            [ type TYPE ] [ scope SCOPE ]
TYPE := { unicast | local | broadcast | multicast | throw |
          unreachable | prohibit | blackhole | nat }
TABLE_ID := [ local | main | default | all | NUMBER ]
SCOPE := [ host | link | global | NUMBER ]
RTPROTO := [ kernel | boot | static | NUMBER ]
```

#### Notes

1. `iif` is not honored (is treated like `dev` and `oif`).
2. Tables are not implemented in macOS (Darwin)
