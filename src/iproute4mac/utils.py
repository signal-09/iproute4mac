import json
import re
import sys
import ipaddress

from _ctypes import PyObj_FromPtr


''' Costants '''
# socket.h
AF_UNSPEC = 0
AF_UNIX = 1
AF_INET = 2
AF_BRIDGE = 7
AF_INET6 = 10
AF_PACKET = 17    # not present in BSD
AF_MPLS = 28

address_families = [
    (AF_UNSPEC, 'none'),
    (AF_INET, 'inet'),
    (AF_INET6, 'inet6'),
    (AF_PACKET, 'link'),
    (AF_MPLS, 'mpls'),
    (AF_BRIDGE, 'bridge')
]

# libc
EXIT_FAILURE = 1
EXIT_SUCCESS = 0

# map operstates
oper_states = {
    'active': 'UP',
    'inactive': 'DOWN'
}

# MAC address RegEx
LLSEG = '[0-9a-fA-F]{1,2}'
LLADDR = '(?:%s(?::%s){5})' % (LLSEG, LLSEG)

# IPv4 RegEx
IPV4SEG = '(?:25[0-5]|2[0-4][0-9]|1{0,1}[0-9]{1,2})'
IPV4ADDR = r'(?:%s(?:\.%s){0,3})' % (IPV4SEG, IPV4SEG)
IPV4MASK = '(?:0x)?(?:[0-9a-fA-F]){8}'

# IPv6 RegEx
IPV6SEG = '(?:[0-9a-fA-F]{1,4})'
IPV6GROUPS = (
    '::',
    '(?:%s:){1,7}:' % (IPV6SEG),
    ':(?::%s){1,7}' % (IPV6SEG),
    '(?:%s:){1,6}:%s' % (IPV6SEG, IPV6SEG),
    '%s:(?::%s){1,6}' % (IPV6SEG, IPV6SEG),
    '(?:%s:){1,5}(?::%s){1,2}' % (IPV6SEG, IPV6SEG),
    '(?:%s:){1,4}(?::%s){1,3}' % (IPV6SEG, IPV6SEG),
    '(?:%s:){1,3}(?::%s){1,4}' % (IPV6SEG, IPV6SEG),
    '(?:%s:){1,2}(?::%s){1,5}' % (IPV6SEG, IPV6SEG),
    '(?:%s:){7,7}%s' % (IPV6SEG, IPV6SEG),
)
IPV6ADDR = '|'.join([f'(?:{group})' for group in IPV6GROUPS[::-1]])
IPV6ADDR = f'(?:{IPV6ADDR})'

# nu <netinet6/nd6.h>
ND6_INFINITE_LIFETIME = 0xffffffff


def stdout(*args, sep='', end=''):
    print(*args, sep=sep, end=end)


def stderr(text):
    sys.stderr.write(text + '\n')


def error(text):
    stderr(f'Error: {text}')
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
    return '???'


def family_name_verbose(family):
    if family == AF_UNSPEC:
        return 'any value'
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
    return sum([bit_count(int(octet)) for octet in mask.split('.')])


def get_addr(name, family):
    if family == AF_MPLS:
        error('MPLS protocol not supported.')
    elif strcmp(name, 'default'):
        if family == AF_INET:
            return Prefix('0.0.0.0/0')
        if family == AF_INET6:
            return Prefix('::/0')
    elif strcmp(name, 'any', 'all'):
        if family == AF_INET:
            return Prefix('0.0.0.0')
        if family == AF_INET6:
            return Prefix('::')
    else:
        prefix = Prefix(name)
        if family == AF_PACKET or prefix.family == family:
            return prefix

    error(f'{family_name_verbose(family)} address is expected rather than "{name}".')


def get_prefix(name, family):
    if family == AF_PACKET:
        error(f'"{name}" may be inet prefix, but it is not allowed in this context.')

    try:
        prefix = get_addr(name, family)
    except ValueError:
        error(f'{family_name_verbose(family)} prefix is expected rather than "{name}".')

    return prefix


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


def delete_keys(data, *args):
    for entry in data:
        for arg in args:
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
    return json.dumps(data, separators=(',', ':'))


def json_unindent_list(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = json_unindent_list(v)
    elif isinstance(obj, list):
        if all(isinstance(x, str) for x in obj):
            return NoIndent(obj)
        for i, l in enumerate(obj):
            obj[i] = json_unindent_list(l)
    return obj


class NoIndent(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        if self.value:
            reps = (repr(v) for v in self.value)
            return '[ ' + ','.join(reps).replace("'", '"') + ' ]'
        return '[ ]'


class IpRouteJSON(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))

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
        json_repr = re.sub(r'\[\n\s+{', '[ {', json_repr)
        json_repr = re.sub(r'},\n\s+{', '},{', json_repr)
        json_repr = re.sub(r'}\n\s*\]', '} ]', json_repr)
        return json_repr


class Prefix:
    __slots__ = ('_prefix')

    def __init__(self, prefix):
        if prefix == 'default':
            prefix = '0.0.0.0/0'
        if '/' in prefix:
            self._prefix = ipaddress.ip_network(prefix)
        else:
            self._prefix = ipaddress.ip_address(prefix)

    def __eq__(self, other):
        if self.version != other.version:
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
        if (isinstance(self._prefix, ipaddress.IPv4Network | ipaddress.IPv6Network)
                and self._prefix.network_address._ip + self._prefix.prefixlen == 0):
            return 'default'
        return str(self._prefix)

    def __str__(self):
        return str(self._prefx)

    @property
    def is_network(self):
        return isinstance(self._prefix, ipaddress.IPv4Network | ipaddress.IPv6Network)

    @property
    def is_address(self):
        return isinstance(self._prefix, ipaddress.IPv4Address | ipaddress.IPv6Address)

    @property
    def is_host(self):
        return self.is_address or self._prefix._prefixlen == self._prefix._max_prefixlen

    @property
    def is_link(self):
        return self._prefix.is_link_local

    @property
    def is_global(self):
        return self._prefix.is_global

    @property
    def address(self):
        if isinstance(self._prefix, ipaddress.IPv4Network | ipaddress.IPv6Network):
            return self._prefix.network_address
        else:
            return self._prefix

    @property
    def prefix(self):
        return self._prefix

    @property
    def prefixlen(self):
        if isinstance(self._prefix, ipaddress.IPv4Network | ipaddress.IPv6Network):
            return self._prefix.prefixlen
        else:
            return self._prefix._max_prefixlen

    @property
    def family(self):
        return AF_INET if self._prefix._version == 4 else AF_INET6

    @property
    def version(self):
        return self._prefix._version


def strcmp(opt, *args):
    return any(arg == opt for arg in args)


def matches(opt, *args):
    return any(arg.startswith(opt) for arg in args)


def matches_color(opt):
    if '=' in opt:
        (opt, arg) = opt.split('=', 1)
    else:
        arg = 'always'
    return '-color'.startswith(opt) and arg in ['always', 'auto', 'never']


def do_notimplemented(argv=[], option={}):
    error('function not implemented')
