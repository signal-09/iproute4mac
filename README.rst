===========
iproute4mac
===========

|CI| |PYPI|

This is a macOS network wrapper to imitate GNU/Linux
`iproute2 <https://wiki.linuxfoundation.org/networking/iproute2>`__
suite, inspired by the
`iproute2mac <https://github.com/brona/iproute2mac>`__ project.

Working staff
=============

Command ``ip``:

============== =========== ========= =============
objects        implemented supported note
============== =========== ========= =============
``address``    yes         yes
``address``    yes         yes
``addrlabel``  no          ?         IPv6 protocol address label
``maddress``   no          ?
``route``      yes         yes
``rule``       no          ?         (e.g. `source based routing with FreeBSD... <https://mmacleod.ca/2011/06/source-based-routing-with-freebsd-using-multiple-routing-table/>`__)
``neighbor``   yes         yes       using `ARP <https://en.wikipedia.org/wiki/Address_Resolution_Protocol>`__ for IPv4 and `NDP <https://en.wikipedia.org/wiki/Neighbor_Discovery_Protocol>`__ for IPv6
``ntable``     no          ?
``ntbl``       no          ?
``link``       yes         yes
``l2tp``       no          ?
``fou``        no          ?         IP-IP tunnel over UDP?
``ila``        no          ?         IPv6 Identifier Locator Addressing
``macsec``     no          no
``tunnel``     no          yes       `IP-IP <https://kovyrin.net/2006/03/17/how-to-create-ip-ip-tunnel-between-freebsd-and-linux/>`__ only
``tuntap``     no          ?         `Tunnelblick <https://github.com/Tunnelblick/Tunnelblick/tree/master/third_party>`__ third party `tuntaposx <https://tuntaposx.sourceforge.net>`__?
``token``      no          ?         May be related to `non-numeric IPv6 mask <https://forums.freebsd.org/threads/how-to-apply-non-numeric-mask-to-ipv6-address.69829/>`__?
``tcpmetrics`` no          ?
``monitor``    no          no
``xfrm``       no          no
``mroute``     no          ?         See `Max OS: no multicast route for 127.0.0.1 <https://issues.redhat.com/browse/JGRP-1808>`__
``mrule``      no          ?
``netns``      no          no
``netconf``    no          yes
``vrf``        no          ?         `Virtual Routing and Forwarding <https://en.wikipedia.org/wiki/Virtual_routing_and_forwarding>`__
``sr``         no          ?         IPv6 Segment Routing management
``nexthop``    no          ?
``mptcp``      no          no        Multipath TCP
``ioam``       no          ?         IPv6 In-situ OAM (IOAM)
``help``       yes         yes
``stats``      no          ?
============== =========== ========= =============

Command ``bridge``:

=========== =========== ========= =============
objects     implemented supported note
=========== =========== ========= =============
``link``    yes         yes       ``show`` only
``fdb``     yes         yes       ``show`` only
=========== =========== ========= =============

Examples:

-  ``ip address [ list | show ]``
-  ``ip address { add | change | replace | delete }``
-  ``ip link [ list | show ]``
-  ``ip link { add | set | change | delete }``
-  ``ip route [ list | show ]``
-  ``ip route { add | change | replace | delete }``
-  ``ip route get``
-  ``ip neigh [ list | show ]``
-  ``ip neigh flush``
-  ``bridge link [ list | show ]``
-  ``bridge fdb [ list | show ]``


Installation
============


Homebrew
--------

The preferred method of installation is `Homebrew <https://brew.sh>`__.

In order to use this tap, you can install directly the package:

.. code:: shell

   brew install signal-09/tap/iproute4mac

Or subscribe the tap
`repository <https://github.com/signal-09/homebrew-tap>`__ and then
install the package:

.. code:: shell

   brew tap signal-09/tap
   brew install iproute4mac


PyPI
----

Create a Virtual Environment and upgrade ``pip`` module:

.. code:: shell

   python3 -m venv venv
   source venv/bin/activate
   python3 -m pip install -U pip

Then install ``iproute4mac``:

.. code:: shell

   python3 -m pip install iproute4mac

Usage
=====

**iproute4mac** try to imitate as much as possible the *look & feel* of
the GNU/Linux iproute2 suite, but macOS (Darwin) is a BSD derivative,
and some aspects cannot be replicated at all.


``ip address show``: look at protocol addresses
-----------------------------------------------

Implemented syntax:

   ip address [ show [ dev IFNAME ] [ master DEVICE \| nomaster ] [ type TYPE ] [up] ]


   TYPE := { bond \| bond_slave \| bridge \| bridge_slave \| **feth**:superscript:`5` \| vlan }

Shows IPv4 and IPv6 addresses assigned to all network interfaces. The
‘show’ subcommand can be omitted:

.. code:: shell

   ip address show

Same as above except that only IPv6 addresses assigned to active network
interfaces are shown:

.. code:: shell

   ip -6 address show up

Shows IPv4 and IPv6 addresses assigned to network interface en0 in
pretty printed JSON:

.. code:: shell

   ip -j -p address show dev en0

Shows IPv4 only addresses assigned to networks member of bridge0:

.. code:: shell

   ip -4 address show master bridge0

Shows IP addresses belonging to private C class network 192.168.0.0/24:

.. code:: shell

   ip address show to 192.168.0.0/24

Note:
^^^^^

1. ``qdisc`` (queuing discipline) is part of the Linux Traffic Control
   subsystem (TC) managed via the ``tc`` utility. Even if this
   information is not reported, similar results in traffic control and
   shaping can be achieved using ``dnctl`` and ``pfctl``.
2. ``address lifetime`` for IPv6 addresses (-L flag of ``ifconfig``) is
   not provided anymore in Sonoma (macOS 14); for IPv4, addresses
   *valid* and *prederred* lifetime, is supposed *forever* (0xffffffff =
   4.294.967.295 = 32 bit).
3. ``sysctl net.inet6.ip6.temppltime`` specifies the “preferred
   lifetime” for privacy addresses, in seconds, and defaults to 86400
   (one day).
4. ``sysctl net.inet6.ip6.tempvltime`` specifies the “valid lifetime”
   for privacy addresses, in second, and defaults to 604800 (one week).
5. ``veth`` can be replaced by ``feth`` in macOS


``ip address add``: add new protocol address
--------------------------------------------


``ip address change``: change protocol address
----------------------------------------------


``ip address replace``: change or add protocol address
------------------------------------------------------

Implemented syntax:

   ip address {add|change|replace} IFADDR dev IFNAME [ LIFETIME ] [
   CONFFLAG-LIST ]

Note:
^^^^^

1. ``{change|replace}`` option “really” change address properties
   (e.g. broadcast) while Linux simply ignore them.


``ip address delete``: delete protocol address
----------------------------------------------


``ip link show``: display device attributes
-------------------------------------------

Implemented syntax:

   ip link show [ DEVICE ] [ up ] [ master DEVICE \| nomaster ] [ type ETYPE ]

   ETYPE := [ TYPE \| bridge_slave \| bond_slave ]

   TYPE := [ bridge \| bond ]

Shows the state of all network interfaces on the system:

.. code:: shell

   ip link show

Shows the bridge devices:

.. code:: shell

   ip link show type bridge

Shows the vlan devices:

.. code:: shell

   ip link show type vlan

Shows devices enslaved by bridge0:

.. code:: shell

   ip link show master bridge0

Note:
^^^^^

1. ``txqlen`` (the transmit queue length) is not configurable on
   specific interface; a system default value is managed via
   ``sysctl net.link.generic.system.sndq_maxlen`` (or
   ``net.link.generic.system.rcvq_maxlen``).


``ip link add``: add virtual link
---------------------------------

Implemented syntax:

   ip link add [ link DEV ] [ name ] NAME [ address LLADDR ] [ mtu MTU ] type TYPE [ ARGS ]

Create a VLAN with TAG 100 linked to en1:

.. code:: shell

   ip link add link en1 name vlan100 type vlan id 100

Create a new bridge interface (auto numbering1):

.. code:: shell

   ip link add type bridge

Create a new bridge with a specified name:

.. code:: shell

   ip link add bridge20 type bridge

Create a new static bond (vs lacp) interface:

.. code:: shell

   ip link add bond1 type bond mode active-backup

Note:
^^^^^

1. macOS ``ifconfig`` print the created interface name to the standard
   output


``ip link delete``: delete virtual link
---------------------------------------

Implemented syntax:

   ip link delete { DEVICE \| dev DEVICE } type TYPE [ ARGS ]

Delete any kind of virtual interface:

.. code:: shell

   ip link del vlan100


``ip link set`` (or ``change``): change device attributes
---------------------------------------------------------

Implemented syntax:


``ip route show``: list routes
------------------------------

Implemented syntax:

   ip route [ show [ SELECTOR ] ]

   SELECTOR := [ proto RTPROTO ] [ type TYPE ] [ scope SCOPE ]

   TYPE := { unicast \| broadcast \| multicast \| blackhole }

   SCOPE := [ host \| link \| global ]

   RTPROTO := [ kernel \| static ]

List routes using a specific gateway:

.. code:: shell

   ip route show via 192.168.0.1

List IPv6 routes using a specific network interface:

.. code:: shell

   ip -6 route show dev en1

List routes for multicast:

.. code:: shell

   ip route show type multicast

List availabe routes to reach specific network:

.. code:: shell

   ip route show to match 192.168.1.0/24

List IPv4 and IPv6 routes2

.. code:: shell

   ip route show table all

Note:
^^^^^

1. ``iif`` is not honored (is treated like ``dev`` and ``oif``).
2. *Route tables* are not implemented in macOS (Darwin), but “table all”
   will result in show IPv4 + IPv6 routes


``ip route add``: add new route
-------------------------------


``ip route delete``: delete route
---------------------------------


``ip route change``: change route
---------------------------------


``ip route replace``: change or add new one
-------------------------------------------

Implemented syntax:

   ip route { add \| delete \| change \| replace } ROUTE

   ROUTE := [ TYPE ] PREFIX [ tos TOS ] [ proto RTPROTO ] [ scope SCOPE ]

   TYPE := { unicast \| broadcast \| multicast \| blackhole }

   SCOPE := [ host \| link \| global ]

   RTPROTO := [ kernel \| boot \| static ]

Add direct routing on a specific network interface:

.. code:: shell

   ip route add 192.168.22.0/24 dev en1

Change interface for a given route:

.. code:: shell

   ip route change 192.168.22.0/24 dev en0

Replace default gateway:

.. code:: shell

   ip route replace default via 192.168.0.254

Delete route:

.. code:: shell

   ip route del 192.168.22.0/24


``ip route get``: get a single route
------------------------------------

Implemented syntax:

   ip route get ADDRESS

Shows the route to reach Google DNS 8.8.8.8:

.. code:: shell

   ip route get 8.8.8.8


``ip neigh show``: list neighbour entries
-----------------------------------------

Note:
^^^^^

1. NOARP and PERMANENT states are not catched


``ip neigh flush``: flush neighbour entries
-------------------------------------------

Same syntax of ``ip neigh show``


Contributing
------------

Every contribute is welcome!


Fork the repository
-------------------

.. figure::
   https://docs.github.com/assets/cb-34352/mw-1440/images/help/repository/fork-button.webp
   :alt: Fork button

   Fork button


Clone the fork
--------------

.. code:: shell

   git clone https://github.com/YOUR-USERNAME/iproute4mac


Create a branch
---------------

Before making changes to the project, you should create a new branch and
check it out (see “`GitHub
flow <https://docs.github.com/en/get-started/using-github/github-flow#following-github-flow>`__”).

.. code:: shell

   git branch BRANCH-NAME
   git checkout BRANCH-NAME


Create a developer environment
------------------------------

.. code:: shell

   python3 -m venv venv
   source venv/bin/activate

Then install requiered packages:

.. code:: shell

   python3 -m pip install -U pip
   python3 -m pip install pre-commit pytest pytest-console-scripts
   pre-commit install


Coding style
------------

`Ruff <https://docs.astral.sh/ruff/>`__ is used to enforce coding style.
You can checkout the compliance with the following command:

.. code:: shell

   pre-commit run --all-files [--show-diff-on-failure]


Commit your work
----------------

Create as few commit as possible to make diff checking easier. In case
of modification of already pushed commit, amend it if possible:

.. code:: shell

   git add -A
   git commit --amend
   git push --force

In case of multiple and not organic commits, “`Squash and
merge <https://docs.github.com/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-commits>`__”
policy will be applied.

.. |CI| image:: https://github.com/signal-09/iproute4mac/actions/workflows/python-package.yml/badge.svg?branch=master
   :target: https://github.com/signal-09/iproute4mac/actions/workflows/python-package.yml

.. |PYPI| image:: https://img.shields.io/pypi/dm/iproute4mac
   :target: https://pypi.org/project/iproute4mac/
