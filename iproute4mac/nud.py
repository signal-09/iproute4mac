import re

import iproute4mac.socket as socket
import iproute4mac.utils as utils

from iproute4mac import OPTION
from iproute4mac.data import _Item, _Items, dict_format, find_item
from iproute4mac.ifconfig import IPV4ADDR, IPV6ADDR, LLADDR, IFNAME
from iproute4mac.prefix import Prefix
from iproute4mac.utils import matches, strcmp


_ARP = "arp"
_NDP = "ndp"

# Neighbour Unreachability Detection
_NUD_NONE = 0x00
_NUD_INCOMPLETE = 0x01
_NUD_REACHABLE = 0x02
_NUD_STALE = 0x04
_NUD_DELAY = 0x08
_NUD_PROBE = 0x10
_NUD_FAILED = 0x20
_NUD_NOARP = 0x40
_NUD_PERMANENT = 0x80

# Linux NUD #, Linux string, macOS flag, macOS desc
_NUD_STATE = [
    (_NUD_NONE, "none", "N", "nostate"),
    (_NUD_INCOMPLETE, "incomplete", "I", "incomplete"),
    (_NUD_REACHABLE, "reachable", "R", "reachable"),
    (_NUD_STALE, "stale", "S", "stale"),
    (_NUD_DELAY, "delay", "D", "delay"),
    (_NUD_PROBE, "probe", "P", "probe"),
    (_NUD_FAILED, "failed", None, None),
    (_NUD_NOARP, "noarp", None, None),
    (_NUD_PERMANENT, "permanent", None, None),
    (None, "waitdelete", "W", "waitdelete"),  # Not present in Linux
    # _NUD_UNUSED = not _NUD_REACHABLE
]


def to_string(value):
    for nud, string, glag, desc in _NUD_STATE:
        if nud == value:
            return string
    raise ValueError


def to_state(value):
    for nud, string, glag, desc in _NUD_STATE:
        if nud == value:
            return string.upper()
    raise ValueError


def to_flag(value):
    for nud, string, flag, desc in _NUD_STATE:
        if nud == value:
            return string
    raise ValueError


def to_desc(value):
    for nud, string, flag, desc in _NUD_STATE:
        if nud == value:
            return desc
    raise ValueError


def from_string(value):
    for nud, string, glag, desc in _NUD_STATE:
        if string == value:
            return nud
    raise ValueError


def from_flag(value):
    for nud, string, flag, desc in _NUD_STATE:
        if flag == value:
            return nud
    raise ValueError


def from_desc(value):
    for nud, string, flag, desc in _NUD_STATE:
        if desc == value:
            return nud
    raise ValueError


def run(*argv, cmd=None):
    res = ""
    if not cmd and OPTION["preferred_family"] != socket._AF_INET6:
        res += utils.shell(_ARP, *argv)
    if not cmd and OPTION["preferred_family"] != socket._AF_INET:
        res += utils.shell(_NDP, *argv)
    if cmd:
        res += utils.shell(cmd, *argv)
    return res


def delete(host, dev=None):
    if host.family == socket._AF_INET:
        utils.shell(_ARP, "-d", host, "ifscope" if dev else None, dev)
    else:
        utils.shell(_NDP, "-d", f"{host}%{dev}" if dev else host)


class _Nud(_Item):
    def __init__(self, dst, lladdr, dev, exp_o, exp_i, state=None, flag=None):
        self._incomplete = lladdr.find("incomplete") > -1
        self._permanent = strcmp("(none)", exp_o, exp_i)
        self._expired = strcmp("expired", exp_o, exp_i)
        self._data = {"dst": Prefix(dst), "dev": dev}
        if not self._incomplete:
            self._data["lladdr"] = lladdr
        # FIXME: how to detect other states (e.g. NOARP)?
        if state:
            state = from_flag(state)
            if flag == "p":
                self._data["proxy"] = None
            elif flag == "R":
                self._data["router"] = None
        else:
            if self._incomplete:
                state = _NUD_FAILED
            elif self._expired:
                state = _NUD_STALE
            else:
                state = _NUD_REACHABLE
        self._data["state"] = [to_state(state)]

    def _format(self, string, *fields, default=None):
        return dict_format(self._data, string, *fields, default=default)

    @property
    def unused(self):
        return to_state(_NUD_REACHABLE) not in self._data["state"]

    def str(self, details=True):
        res = str(self._data["dst"])
        res += self._format(" dev {}", "dev")
        res += self._format(" lladdr {}", "lladdr")
        for key in ["router", "proxy"]:
            res += self._format(f" {key}", key)
        res += f" {self._data['state'][0]}"
        return res


class Nud:
    __slots__ = "_nuds"

    _arp = re.compile(
        rf"^(?P<dst>{IPV4ADDR})"
        rf"\s+(?P<lladdr>(?:\(incomplete\)|{LLADDR}))"
        r"\s+(?P<exp_o>\S+)"
        r"\s+(?P<exp_i>\S+)"
        rf"\s+(?P<dev>{IFNAME})"
        r"(?:\s+(?P<refs>\d+)?)?"
        r"(?:\s+(?P<probes>\d+)?)?",
        re.MULTILINE,
    )
    _ndp = re.compile(
        rf"^(?P<dst>{IPV6ADDR})(?:%\w+)?"
        rf"\s+(?P<lladdr>(?:\(incomplete\)|{LLADDR}))"
        rf"\s+(?P<dev>{IFNAME})"
        r"\s+(?P<exp_o>\S+)"
        r"\s+(?P<exp_i>\S+)"
        r"\s+(?P<state>\w)"
        r"(?:\s+(?P<flag>\w)?)?"
        r"(?:\s+(?P<probes>\d+)?)?",
        re.MULTILINE,
    )

    def __init__(self):
        self._nuds = []
        res = utils.shell(_ARP, "-n", "-l", "-a")
        for nud in self._arp.finditer(res):
            dst, lladdr, exp_o, exp_i, dev, refs, probes = nud.groups()
            self._nuds.append(_Nud(dst, lladdr, dev, exp_o, exp_i))
        res = utils.shell(_NDP, "-n", "-l", "-a")
        for nud in self._ndp.finditer(res):
            dst, lladdr, dev, exp_o, exp_i, state, flag, probes = nud.groups()
            self._nuds.append(_Nud(dst, lladdr, dev, exp_o, exp_i, state, flag))

    def __iter__(self):
        for nud in self._nuds:
            yield nud

    def __str__(self):
        return "\n".join(map(str, self._nuds))

    def __len__(self):
        return len(self._nuds)

    def __getitem__(self, index):
        return self._nuds[index]

    def pop(self, index=-1):
        return self._nuds.pop(index)

    def set(self, nuds):
        if not isinstance(nuds, list) or not all(isinstance(n, _Nud) for n in nuds):
            raise ValueError("argument is not list() of <class 'nud._Nud'>")
        self._nuds = nuds

    def dict(self, details=None):
        """
        List nud dictiornaries
        """
        return [n.dict(details=details) for n in self._nuds]

    def str(self, details=None):
        return "\n".join([nud.str(details=details) for nud in self._nuds])
