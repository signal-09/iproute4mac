import json
import re
import sys

from _ctypes import PyObj_FromPtr


''' Costants '''
# socket.h
AF_UNSPEC = 0
AF_UNIX = 1
AF_INET = 2
AF_BRIDGE = 7
AF_INET6 = 10
AF_PACKET = 17    # not present in BSD
AF_INET6 = 26
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
MACSEG = r'[0-9a-fA-F]{1,2}'
MACADDR = r'(?:%s(?::%s){5})' % (MACSEG, MACSEG)

# IPv4 RegEx
IPV4SEG = r'(?:25[0-5]|2[0-4][0-9]|1{0,1}[0-9]{1,2})'
IPV4ADDR = r'(?:%s(?:\.%s){0,3})' % (IPV4SEG, IPV4SEG)

# IPv6 RegEx
IPV6SEG = r'(?:[0-9a-fA-F]{1,4})'
IPV6GROUPS = (
    r'::',
    r'(?:%s:){1,7}:' % (IPV6SEG),
    r':(?::%s){1,7}' % (IPV6SEG),
    r'(?:%s:){1,6}:%s' % (IPV6SEG, IPV6SEG),
    r'%s:(?::%s){1,6}' % (IPV6SEG, IPV6SEG),
    r'(?:%s:){1,5}(?::%s){1,2}' % (IPV6SEG, IPV6SEG),
    r'(?:%s:){1,4}(?::%s){1,3}' % (IPV6SEG, IPV6SEG),
    r'(?:%s:){1,3}(?::%s){1,4}' % (IPV6SEG, IPV6SEG),
    r'(?:%s:){1,2}(?::%s){1,5}' % (IPV6SEG, IPV6SEG),
    r'(?:%s:){7,7}%s' % (IPV6SEG, IPV6SEG),
)
IPV6ADDR = '|'.join(['(?:%s)' % (g) for g in IPV6GROUPS[::-1]])
IPV6ADDR = r'(?:%s)(?:%%\w+)?' % IPV6ADDR

# nu <netinet6/nd6.h>
ND6_INFINITE_LIFETIME = 0xffffffff


def stdout(*args, sep='', end=''):
    print(*args, sep=sep, end=end)


def stderr(text):
    sys.stderr.write(text + '\n')


def error(text):
    stderr('Error: %s' % text)
    exit(-1)


def missarg(key):
    error('argument "%s" is required' % key)


def invarg(msg, arg):
    error('argument "%s" is wrong: %s' % (arg, msg))


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


def delete_keys(data, attr):
    for d in data:
        for a in attr:
            d.pop(a, None)


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
    else:
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
            json_repr = json_repr.replace('"{}"'.format(format_spec.format(id)), repr(ref(id)))
        json_repr = re.sub(r'\[\n\s+{', r'[ {', json_repr)
        json_repr = re.sub(r'},\n\s+{', r'},{', json_repr)
        json_repr = re.sub(r'}\n\s*\]', r'} ]', json_repr)
        return json_repr


def matches_color(opt):
    if '=' in opt:
        (opt, arg) = opt.split('=', 1)
    else:
        arg = 'always'
    return '-color'.startswith(opt) and arg in ['always', 'auto', 'never']


def do_notimplemented(argv=[], option={}):
    error('function not implemented')
