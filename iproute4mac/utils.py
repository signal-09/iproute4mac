import ipaddress
import json
import re
import socket
import subprocess
import sys

from _ctypes import PyObj_FromPtr


""" Costants """
# socket.h
AF_UNSPEC = 0
AF_UNIX = 1
AF_INET = 2
AF_BRIDGE = 7
AF_INET6 = 10
AF_PACKET = 17  # not present in BSD
AF_MPLS = 28

address_families = [
    (AF_UNSPEC, "none"),
    (AF_INET, "inet"),
    (AF_INET6, "inet6"),
    (AF_PACKET, "link"),
    (AF_MPLS, "mpls"),
    (AF_BRIDGE, "bridge"),
]

# libc
EXIT_FAILURE = 1
EXIT_SUCCESS = 0

# map operstates
oper_states = {"active": "UP", "inactive": "DOWN"}

# MAC address RegEx
LLSEG = "[0-9a-fA-F]{1,2}"
LLADDR = "(?:%s(?::%s){5})" % (LLSEG, LLSEG)

# IPv4 RegEx
IPV4SEG = "(?:25[0-5]|2[0-4][0-9]|1{0,1}[0-9]{1,2})"
IPV4ADDR = r"(?:%s(?:\.%s){0,3})" % (IPV4SEG, IPV4SEG)
IPV4MASK = "(?:0x)?(?:[0-9a-fA-F]){8}"

# IPv6 RegEx
IPV6SEG = "(?:[0-9a-fA-F]{1,4})"
IPV6GROUPS = (
    "::",
    "(?:%s:){1,7}:" % (IPV6SEG),
    ":(?::%s){1,7}" % (IPV6SEG),
    "(?:%s:){1,6}:%s" % (IPV6SEG, IPV6SEG),
    "%s:(?::%s){1,6}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,5}(?::%s){1,2}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,4}(?::%s){1,3}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,3}(?::%s){1,4}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,2}(?::%s){1,5}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){7,7}%s" % (IPV6SEG, IPV6SEG),
)
IPV6ADDR = "|".join([f"(?:{group})" for group in IPV6GROUPS[::-1]])
IPV6ADDR = f"(?:{IPV6ADDR})"

# nu <netinet6/nd6.h>
ND6_INFINITE_LIFETIME = 0xFFFFFFFF


def stdout(*argv, sep="", end=""):
    print(*argv, sep=sep, end=end)


def stderr(text):
    if text[-1] != "\n":
        text += "\n"
    sys.stderr.write(text)


def error(text):
    stderr(f"Error: {text}")
    exit(-1)


def missarg(key):
    error(f'argument "{key}" is required')


def invarg(msg, arg):
    error(f'argument "{arg}" is wrong: {msg}')


def incomplete_command():
    stderr('Command line is not complete. Try option "help"')
    exit(-1)


def next_arg(argv):
    try:
        return argv.pop(0)
    except IndexError:
        incomplete_command()


def read_family(name):
    for f, n in address_families:
        if name == n:
            return f
    return AF_UNSPEC


def family_name(family):
    for f, n in address_families:
        if family == f:
            return n
    return "???"


def family_name_verbose(family):
    if family == AF_UNSPEC:
        return "any value"
    return family_name(family)


def af_bit_len(af):
    if af == AF_INET6:
        return 128
    elif af == AF_INET:
        return 32
    elif af == AF_MPLS:
        return 20
    else:
        return 0


def af_byte_len(af):
    return int(af_bit_len(af) / 8)


def mask2bits(mask):
    return sum([bit_count(int(octet)) for octet in mask.split(".")])


def get_addr(name, family):
    if family == AF_MPLS:
        error("MPLS protocol not supported.")
    elif strcmp(name, "default"):
        if family == AF_INET:
            return Prefix("0.0.0.0/0")
        if family == AF_INET6:
            return Prefix("::/0")
        return Prefix("default")
    elif strcmp(name, "any", "all"):
        if family == AF_INET:
            return Prefix("0.0.0.0")
        if family == AF_INET6:
            return Prefix("::")
        return Prefix("any")
    else:
        addr = Prefix(name)
        if family in (AF_UNSPEC, AF_PACKET) or addr.family == family:
            return addr

    error(f'{family_name_verbose(family)} address is expected rather than "{name}".')


def get_prefix(name, family):
    if family == AF_PACKET:
        error(f'"{name}" may be inet prefix, but it is not allowed in this context.')

    try:
        prefix = get_addr(name, family)
    except ValueError:
        error(f'{family_name_verbose(family)} prefix is expected rather than "{name}".')

    return prefix


def get_prefsrc(host, family):
    family = socket.AF_INET6 if ":" in host or family == AF_INET6 else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_DGRAM)
    sock.connect((host, 7))
    src = sock.getsockname()[0]
    sock.close()
    return src


def recurse_in(data, attr, val):
    var = attr.pop(0)
    if attr:
        if var in data:
            if isinstance(data[var], dict):
                return recurse_in(data[var], attr, val)
            elif isinstance(data[var], list):
                return val in data[var]
    else:
        if var in data:
            if isinstance(data[var], list):
                return val in data[var]
            return data[var] == val

    return False


def delete_keys(data, *argv):
    for entry in data:
        for arg in argv:
            entry.pop(arg, None)


# int.bit_count() only in Python >=3.10
def bit_count(self):
    return bin(self).count("1")


def netmask_to_length(mask):
    return bit_count(int(mask, 16))


def ref(obj_id):
    return PyObj_FromPtr(obj_id)


def json_dumps(data, pretty=False):
    if pretty:
        return json.dumps(data, cls=IpRouteJSON, indent=4)
    return json.dumps(data, separators=(",", ":"))


def json_unindent_list(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = json_unindent_list(v)
    elif isinstance(obj, list):
        if all(isinstance(x, str) for x in obj):
            return NoIndent(obj)
        for index, entry in enumerate(obj):
            obj[index] = json_unindent_list(entry)
    return obj


class NoIndent(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        if self.value:
            reps = (repr(v) for v in self.value)
            return "[ " + ",".join(reps).replace("'", '"') + " ]"
        return "[ ]"


class IpRouteJSON(json.JSONEncoder):
    FORMAT_SPEC = "@@{}@@"
    regex = re.compile(FORMAT_SPEC.format(r"(\d+)"))

    def default(self, obj):
        if isinstance(obj, NoIndent):
            return self.FORMAT_SPEC.format(id(obj))
        return super(IpRouteJSON, self).default(obj)

    def encode(self, obj):
        obj = json_unindent_list(obj)
        format_spec = self.FORMAT_SPEC
        json_repr = super(IpRouteJSON, self).encode(obj)
        for match in self.regex.finditer(json_repr):
            id = int(match.group(1))
            json_repr = json_repr.replace(f'"{format_spec.format(id)}"', repr(ref(id)))
        json_repr = re.sub(r"\[\n\s+{", "[ {", json_repr)
        json_repr = re.sub(r"},\n\s+{", "},{", json_repr)
        json_repr = re.sub(r"}\n\s*\]", "} ]", json_repr)
        return json_repr


class Prefix:
    __slots__ = ("_prefix", "_any")

    def __init__(self, prefix):
        if prefix == "default":
            self._prefix = None
            self._any = False
        elif prefix == "any":
            self._prefix = None
            self._any = True
        elif "/" in prefix:
            self._prefix = ipaddress.ip_network(prefix)
            self._any = False
        else:
            self._prefix = ipaddress.ip_address(prefix)
            self._any = False

    def __eq__(self, other):
        if self.family != other.family:
            return False
        if isinstance(type(self._prefix), type(other.prefix)):
            return self._prefix == other.prefix
        if self.is_host and other.is_host:
            return self.address == other.address
        return False

    def __contains__(self, other):
        if isinstance(self._prefix, ipaddress.IPv4Network | ipaddress.IPv6Network):
            if other.is_host:
                return other.address in self._prefix
            else:
                return other.prefix.subnet_of(self._prefix)
        elif other.is_host:
            return other.address == self._prefix
        return False

    def __repr__(self):
        if self.is_default:
            return "default"
        if self.is_any:
            return "any"
        return str(self._prefix)

    def __str__(self):
        if self._prefix:
            return str(self._prefix)
        if self.is_any:
            return "any"
        return "default"

    @property
    def _max_prefixlen(self):
        return self._prefix._max_prefixlen

    @property
    def _is_default(self):
        return not self._prefix and not self._any

    @property
    def _is_any(self):
        return not self._prefix and self._any

    @property
    def _is_network(self):
        return isinstance(self._prefix, ipaddress.IPv4Network | ipaddress.IPv6Network)

    @property
    def _is_address(self):
        return isinstance(self._prefix, ipaddress.IPv4Address | ipaddress.IPv6Address)

    @property
    def is_default(self):
        return self._is_default or (self._is_network and self._prefix.network_address._ip + self._prefix.prefixlen == 0)

    @property
    def is_any(self):
        return self._is_any or (self._is_address and self._prefix._ip == 0)

    @property
    def is_network(self):
        return self._is_network or self._is_default

    @property
    def is_address(self):
        return self._is_address or self._is_any

    @property
    def is_host(self):
        return self._is_address or (self._is_network and self._prefix._prefixlen == self._prefix._max_prefixlen)

    @property
    def is_link(self):
        return self._prefix and self._prefix.is_link_local

    @property
    def is_global(self):
        return self._is_default or (self._prefix and self._prefix.is_global)

    @property
    def address(self):
        if self._is_network:
            return self._prefix.network_address
        else:
            # Return None in case of default/any
            return self._prefix

    @property
    def prefix(self):
        return self._prefix

    @property
    def prefixlen(self):
        if self._is_default:
            return 0
        if self._is_network:
            return self._prefix.prefixlen
        if self._is_address:
            return self._prefix._max_prefixlen
        raise ValueError("Unknown prefix length")

    @property
    def family(self):
        if not self._prefix:
            return AF_UNSPEC
        if self._prefix._version == 6:
            return AF_INET6
        return AF_INET

    @family.setter
    def family(self, value):
        if value not in (AF_INET, AF_INET6):
            raise ValueError(f"'{value!r}' does not appear to be a valid address family")
        if self._prefix:
            raise ValueError("Address family cannot be assigned to an already initialized prefix")
        if self._is_default:
            if value == AF_INET:
                self._prefix = ipaddress.ip_network("0.0.0.0/0")
            else:
                self._prefix = ipaddress.ip_network("::/0")
        elif self._is_any:
            if value == AF_INET:
                self._prefix = ipaddress.ip_address("0.0.0.0")
            else:
                self._prefix = ipaddress.ip_address("::")
            self._any = False

    @property
    def version(self):
        return self._prefix._version if self._prefix else AF_UNSPEC

    @version.setter
    def version(self, value):
        if value not in (4, 6):
            raise ValueError(f"'{value!r}' does not appear to be a valid IP version protocol")
        if self._prefix:
            raise ValueError("IP version protocol cannot be assigned to an already initialized prefix")
        self.family = AF_INET if value == 4 else AF_INET6


def strcmp(opt, *argv):
    return any(arg == opt for arg in argv)


def matches(opt, *argv):
    return any(arg.startswith(opt) for arg in argv)


def startwith(opt, *argv):
    return any(opt.startswith(arg) for arg in argv)


def matches_color(opt):
    if "=" in opt:
        (opt, arg) = opt.split("=", 1)
    else:
        arg = "always"
    return "-color".startswith(opt) and arg in ["always", "auto", "never"]


def do_notimplemented(argv=[], option={}):
    error("function not implemented")


def flat_touple(*argv):
    args = ()
    for arg in argv:
        if isinstance(arg, list):
            args += tuple(arg)
        elif isinstance(arg, tuple):
            args += arg
        else:
            args += (arg,)
    return args


def shell(*argv):
    args = flat_touple(*argv)
    cmd = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    if cmd.returncode != 0:
        stderr(cmd.stderr)
        exit(cmd.returncode)
    return cmd.stdout
