from iproute4mac.utils import *

_ARP = "arp"
_NDP = "ndp"

# Neighbour Unreachability Detection
NUD_NONE = 0x00
NUD_INCOMPLETE = 0x01
NUD_REACHABLE = 0x02
NUD_STALE = 0x04
NUD_DELAY = 0x08
NUD_PROBE = 0x10
NUD_FAILED = 0x20
NUD_NOARP = 0x40
NUD_PERMANENT = 0x80

# Linux NUD #, Linux string, macOS flag, macOS desc
NUD_STATE = [
    (NUD_NONE, "none", "N", "nostate"),
    (NUD_INCOMPLETE, "incomplete", "I", "incomplete"),
    (NUD_REACHABLE, "reachable", "R", "reachable"),
    (NUD_STALE, "stale", "S", "stale"),
    (NUD_DELAY, "delay", "D", "delay"),
    (NUD_PROBE, "probe", "P", "probe"),
    (NUD_FAILED, "failed", None, None),
    (NUD_NOARP, "noarp", None, None),
    (NUD_PERMANENT, "permanent", None, None),
    (None, "waitdelete", "W", "waitdelete"),  # Not present in Linux
    # NUD_UNUSED = not NUD_REACHABLE
]


def to_string(value):
    for nud, string, glag, desc in NUD_STATE:
        if nud == value:
            return string
    raise ValueError


def to_state(value):
    for nud, string, glag, desc in NUD_STATE:
        if nud == value:
            return string.upper()
    raise ValueError


def to_flag(value):
    for nud, string, flag, desc in NUD_STATE:
        if nud == value:
            return string
    raise ValueError


def to_desc(value):
    for nud, string, flag, desc in NUD_STATE:
        if nud == value:
            return desc
    raise ValueError


def from_string(value):
    for nud, string, glag, desc in NUD_STATE:
        if string == value:
            return nud
    raise ValueError


def from_flag(value):
    for nud, string, flag, desc in NUD_STATE:
        if flag == value:
            return nud
    raise ValueError


def from_desc(value):
    for nud, string, flag, desc in NUD_STATE:
        if desc == value:
            return nud
    raise ValueError


def exec(*argv, cmd=None):
    res = ""
    if not cmd and OPTION["preferred_family"] != AF_INET6:
        res += shell(_ARP, *argv)
    if not cmd and OPTION["preferred_family"] != AF_INET:
        res += shell(_NDP, *argv)
    if cmd:
        res += shell(cmd, *argv)
    return res


def delete(host, dev=None):
    if host.family == AF_INET:
        exec("-d", str(host), "ifscope" if dev else None, dev, cmd=_ARP)
    else:
        exec("-d", f"{host}%{dev}" if dev else str(host), cmd=_NDP)


def dumps(entries):
    if OPTION["json"]:
        print(json_dumps(entries, OPTION["pretty"]))
        return

    for entry in entries:
        stdout(entry["dst"])
        if "dev" in entry:
            stdout(f" dev {entry['dev']}")
        if "lladdr" in entry:
            stdout(f" lladdr {entry['lladdr']}")
        for state in entry["state"]:
            stdout(f" {state}")
        stdout(end="\n")


class nudRegEx:
    __slots__ = ("_nud", "_incomplete", "_permanent", "_expired")
    _ipv4 = re.compile(
        rf"(?P<dst>{IPV4ADDR})"
        rf"\s+(?P<lladdr>(?:\(incomplete\)|{LLADDR}))"
        r"\s+(?P<exp_o>\S+)"
        r"\s+(?P<exp_i>\S+)"
        r"\s+(?P<dev>\w+)"
    )
    _ipv6 = re.compile(
        rf"(?P<dst>{IPV6ADDR})(?:%\w+)?"
        rf"\s+(?P<lladdr>(?:\(incomplete\)|{LLADDR}))"
        r"\s+(?P<dev>\w+)"
        r"\s+(?P<exp_o>\S+)"
        r"\s+(?P<exp_i>\S+)"
        r"\s+(?P<state>\w)"
        r"\s+(?P<flag>\w)?"
    )

    def __init__(self, line):
        entry = self._ipv4.match(line)
        if not entry:
            if not (entry := self._ipv6.match(line)):
                raise ValueError
        self._nud = entry.groupdict()
        self._nud["dst"] = Prefix(self._nud["dst"])
        self._incomplete = self._nud["lladdr"].find("incomplete") > -1
        self._permanent = strcmp("(none)", self._nud["exp_o"], self._nud["exp_i"])
        self._expired = strcmp("expired", self._nud["exp_o"], self._nud["exp_i"])
        del self._nud["exp_o"]
        del self._nud["exp_i"]
        if self._incomplete:
            del self._nud["lladdr"]
        # FIXME: how to detect other states (e.g. NOARP)?
        if "state" in self._nud:
            state = from_flag(self._nud["state"])
            if self._nud["flag"] == "p":
                self._nud["proxy"] = None
            if self._nud["flag"] == "R":
                self._nud["router"] = None
            del self._nud["flag"]
        else:
            if self._incomplete:
                state = NUD_FAILED
            elif self._expired:
                state = NUD_STALE
            else:
                state = NUD_REACHABLE
        self._nud["state"] = [to_state(state)]

    def to_dict(self):
        return self._nud


def parse(res):
    entries = []
    for line in iter(res.split("\n")):
        try:
            nud = nudRegEx(line)
        except ValueError:
            debug(f'Unparsed line "{line.strip()}"')
            continue
        entries.append(nud.to_dict())

    return entries
