# iproute4mac

[![GH Actions CI](https://github.com/signal-09/iproute4mac/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/signal-09/iproute4mac/actions/workflows/python-package.yml)

This is a macOS network wrapper to imitate GNU/Linux [iproute2](https://wiki.linuxfoundation.org/networking/iproute2) suite, inspired by the [iproute2mac](https://github.com/brona/iproute2mac) project.

> **WARNING:** early Aplha stage
>
> Read only `ip link [show]`, `ip address [show]`, and `ip route [show]` objects implemented for now.

## Installation

### Homebrew

The preferred method of installation is [Homebrew](https://brew.sh).

In order to use this tap, you can install directly the package:

```shell
brew install signal-09/tap/iproute4mac
```

Or subscribe the tap [repository](https://github.com/signal-09/homebrew-tap) and then install the package:

```shell
brew tap signal-09/tap
brew install iproute4mac
```

#### Installing latest Git version (`HEAD`)

You can install the latest Git version by adding the `--HEAD` option:

```shell
brew install signal-09/tap/iproute4mac --HEAD
```

### PyPI

Create a Virtual Environment and upgrade `pip` module:

```shell
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -U pip
```

Then install `iproute4mac`:

```shell
python3 -m pip install iproute4mac
```

## Usage

**iproute4mac** try to imitate as much as possible the *look & feel* of the GNU/Linux iproute2 suite, but macOS (Darwin) is a BSD derivative, and some aspects cannot be replicated at all.

### `ip address show`: look at protocol addresses

Implemented syntax:

> ip address [ show [ dev IFNAME ] [ ~~scope SCOPE-ID~~ ] [ master DEVICE | nomaster ]
>                   [ type TYPE ] [ ~~to PREFIX~~ ] [ ~~FLAG-LIST~~ ]
>                   [ ~~label LABEL~~ ] [up] [ ~~vrf NAME~~ ] ]
>
> ~~SCOPE-ID := [ host | link | global | NUMBER ]~~
>
> ~~FLAG-LIST := [ FLAG-LIST ] FLAG~~
>
> ~~FLAG  := [ permanent | dynamic | secondary | primary |
>            [-]tentative | [-]deprecated | [-]dadfailed | temporary |
>            CONFFLAG-LIST ]~~
>
> ~~CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG~~
>
> ~~CONFFLAG  := [ home | nodad | mngtmpaddr | noprefixroute | autojoin ]~~
>
> TYPE := { ~~bareudp~~ | bond | bond_slave | bridge | bridge_slave |
>           ~~dummy~~ | ~~erspan~~ | ~~geneve~~ | ~~gre~~ | ~~gretap~~ | ~~ifb~~ |
>           ~~ip6erspan~~ | ~~ip6gre~~ | ~~ip6gretap~~ | ~~ip6tnl~~ |
>           ~~ipip~~ | ~~ipoib~~ | ~~ipvlan~~ | ~~ipvtap~~ |
>           ~~macsec~~ | ~~macvlan~~ | ~~macvtap~~ |
>           ~~netdevsim~~ | ~~nlmon~~ | ~~rmnet~~ | ~~sit~~ | ~~team~~ | ~~team_slave~~ |
>           ~~vcan~~ | ~~veth~~ | vlan | ~~vrf~~ | ~~vti~~ | ~~vxcan~~ | ~~vxlan~~ | ~~wwan~~ |
>           ~~xfrm~~ }

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

1. `qdisc` (queuing discipline) is part of the Linux Traffic Control subsystem (TC) managed via the `tc` utility. Even if this information is not reported, similar results in traffic control and shaping can be achieved using `dnctl` and `pfctl`.
2. `address lifetime` for IPv6 addresses (-L flag of `ifconfig`) is not provided anymore in Sonoma (macOS 14); for IPv4, addresses *valid* and *prederred* lifetime, is supposed *forever* (0xffffffff = 4.294.967.295 = 32 bit).

### `ip link show`: display device attributes

Implemented syntax:

> ip link show [ DEVICE | ~~group GROUP~~ ] [ up ] [ master DEVICE | nomaster ] [ type ETYPE ] [ ~~vrf NAME~~ ]
>
> ETYPE := [ TYPE | bridge_slave | bond_slave ]
>
> TYPE := [ bridge | bond | ~~can~~ | ~~dummy~~ | ~~hsr~~ | ~~ifb~~ | ~~ipoib~~ | ~~macvlan~~ | ~~macvtap~~
>         | ~~vcan~~ | ~~vxcan~~ | ~~veth~~ | vlan | ~~vxlan~~ | ~~ip6tnl~~ | ~~ipip~~ | ~~sit~~ | ~~gre~~
>         | ~~gretap~~ | ~~erspan~~ | ~~ip6gre~~ | ~~ip6gretap~~ | ~~ip6erspan~~ | ~~vti~~ | ~~nlmon~~
>         | ~~ipvlan~~ | ~~ipvtap~~ | ~~lowpan~~ | ~~geneve~~ | ~~bareudp~~ | ~~vrf~~ | ~~macsec~~
>         | ~~netdevsim~~ | ~~rmnet~~ | ~~xfrm~~ ]

Shows the state of all network interfaces on the system:

```shell
ip link show
```

Shows the bridge devices:

```shell
ip link show type bridge
```

Shows the vlan devices:
```shell
ip link show type vlan
```

Shows devices enslaved by bridge0
```shell
ip link show master bridge0
```

### `ip route add`: add new route
### `ip route change`: change route
### `ip route replace`: change or add new one

Implemented syntax:

> ip route { add | del | change | ~~append~~ | replace } ROUTE
>
> ROUTE := NODE_SPEC [ INFO_SPEC ]
>
> NODE_SPEC := [ TYPE ] PREFIX [ tos TOS ]
>              [ ~~table TABLE_ID~~ ] [ proto RTPROTO ]
>              [ scope SCOPE ] [ metric METRIC ]
>              [ ~~ttl-propagate { enabled | disabled }~~ ]
>
> INFO_SPEC := { ~~NH | nhid ID~~ } OPTIONS FLAGS [ ~~nexthop NH~~ ]...
>
> NH := [ encap ENCAPTYPE ENCAPHDR ] [ via [ FAMILY ] ADDRESS ]
>       [ dev STRING ] [ weight NUMBER ] NHFLAGS
>
> FAMILY := [ inet | inet6 | mpls | bridge | link ]
>
> OPTIONS := FLAGS [ mtu NUMBER ] [ ~~advmss NUMBER~~ ] [ as [ to ] ADDRESS ]
>            [ rtt TIME ] [ rttvar TIME ] [ ~~reordering NUMBER~~ ]
>            [ ~~window NUMBER~~ ] [ ~~cwnd NUMBER~~ ] [ ~~initcwnd NUMBE~~R ]
>            [ ssthresh NUMBER ] [ ~~realms REALM~~ ] [ ~~src ADDRESS~~ ]
>            [ ~~rto_min TIME~~ ] [ hoplimit NUMBER ] [ ~~initrwnd NUMBER~~ ]
>            [ ~~features FEATURES~~ ] [ ~~quickack BOOL~~ ] [ ~~congctl NAME~~ ]
>            [ ~~pref PREF~~ ] [ expires TIME ] [ ~~fastopen_no_cookie BOOL~~ ]
>
> TYPE := { unicast | local | broadcast | multicast | throw |
>           unreachable | prohibit | blackhole | nat }
>
> TABLE_ID := [ local | main | default | all | NUMBER ]
>
> SCOPE := [ host | link | global | NUMBER ]
>
> NHFLAGS := [ onlink | pervasive ]
>
> RTPROTO := [ kernel | boot | static | NUMBER ]
>
> PREF := [ low | medium | high ]
>
> TIME := NUMBER[s|ms]
>
> BOOL := [1|0]
>
> FEATURES := ecn
>
> ENCAPTYPE := [ mpls | ip | ip6 | seg6 | seg6local | rpl | ioam6 ]
>
> ENCAPHDR := [ MPLSLABEL | SEG6HDR | SEG6LOCAL | IOAM6HDR ]
>
> SEG6HDR := [ mode SEGMODE ] segs ADDR1,ADDRi,ADDRn [hmac HMACKEYID] [cleanup]
>
> SEGMODE := [ encap | inline ]
>
> SEG6LOCAL := action ACTION [ OPTIONS ] [ count ]
>
> ACTION := { End | End.X | End.T | End.DX2 | End.DX6 | End.DX4 |
>             End.DT6 | End.DT4 | End.DT46 | End.B6 | End.B6.Encaps |
>             End.BM | End.S | End.AS | End.AM | End.BPF }
>
> OPTIONS := OPTION [ OPTIONS ]
>
> OPTION := { srh SEG6HDR | nh4 ADDR | nh6 ADDR | iif DEV | oif DEV |
>             table TABLEID | vrftable TABLEID | endpoint PROGNAME }
>
> IOAM6HDR := trace prealloc type IOAM6_TRACE_TYPE ns IOAM6_NAMESPACE size IOAM6_TRACE_SIZE

Add direct routing on a specific network interface:

```shell
ip route add 192.168.22.0/24 dev en1
```

Change interface for a given route:
```shell
ip route change 192.168.22.0/24 dev en0
```

Replace default gateway:

```shell
ip route replace default via 192.168.0.254
```

Delete route:

```shell
ip route del 192.168.22.0/24
```

### `ip route show`: list routes

Implemented syntax:

> ip route [ show [ SELECTOR ] ]
>
> SELECTOR := [ ~~root PREFIX~~ ] [ ~~match PREFIX~~ ] [ ~~exact PREFIX~~ ]
>             [ ~~table TABLE_ID~~ ] [ ~~vrf NAME~~ ] [ proto RTPROTO ]
>             [ type TYPE ] [ scope SCOPE ]
>
> TYPE := { unicast | ~~local~~ | broadcast | multicast | ~~throw~~ |
>           ~~unreachable~~ | ~~prohibit~~ | blackhole | ~~nat~~ }
>
> ~~TABLE_ID := [ local | main | default | all | NUMBER ]~~
>
> SCOPE := [ host | link | global | ~~NUMBER~~ ]
>
> RTPROTO := [ kernel | ~~boot~~ | static | ~~NUMBER~~ ]

List routes using a specific gateway:

```shell
ip route show via 192.168.0.1
```

List routes using a specific network interface:

```shell
ip route show dev en1
```

List routes for multicast:

```shell
ip route show type multicast
```

#### Notes

1. `iif` is not honored (is treated like `dev` and `oif`).
2. *Route tables* are not implemented in macOS (Darwin).

### `ip route get`: get a single route

Implemented syntax:

> ip route get ~~ROUTE_GET_FLAGS~~ ADDRESS [ ~~from ADDRESS iif STRING~~  ] [ ~~oif STRING~~ ] [ ~~mark MARK~~ ] [ ~~tos TOS~~ ] [ ~~vrf NAME~~ ] [ ~~ipproto PROTOCOL~~ ] [ ~~sport NUMBER~~ ] [ ~~dport NUMBER~~ ]
> ROUTE_GET_FLAGS :=  [ fibmatch ]

Shows the route to reach Google DNS 8.8.8.8:

```shell
ip route get 8.8.8.8
```

## Contributing

Every contribute is welcome!

### Fork the repository

![Fork button](https://docs.github.com/assets/cb-34352/mw-1440/images/help/repository/fork-button.webp "Fork")

### Clone the fork

```shell
git clone https://github.com/YOUR-USERNAME/iproute4mac
```

### Create a branch

Before making changes to the project, you should create a new branch and check it out (see "[GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow#following-github-flow)").

```shell
git branch BRANCH-NAME
git checkout BRANCH-NAME
```

### Create a developer environment

```shell
python3 -m venv venv
source venv/bin/activate
```

Then install requiered packages:

```shell
python3 -m pip install -U pip
python3 -m pip install pre-commit pytest flake8
pre-commit install
```

### Coding style

[Ruff](https://docs.astral.sh/ruff/) is used to enforce coding style.
You can checkout the compliance with the following command:

```shell
pre-commit run --all-files [--show-diff-on-failure]
```

### Commit your work

Create as few commit as possible to make diff checking easier. In case of modification of already pushed commit, amend it if possible:

```shell
git add -A
git commit --amend
git push --force
```

In case of multiple and not organic commits, "[Squash and merge](https://docs.github.com/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-commits)" policy will be applied.
