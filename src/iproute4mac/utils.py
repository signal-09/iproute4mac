import json
import re
import sys

from _ctypes import PyObj_FromPtr


''' Costants '''
# Linux Address families
AF_UNSPEC = 0
AF_INET   = 2
AF_BRIDGE = 7
AF_INET6  = 10
AF_PACKET = 17 # not present in BSD
AF_INET6  = 26
AF_MPLS   = 28

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

# maps operstates
oper_states = {
    'active': 'UP',
    'inactive': 'DOWN'
}


''' Utilities '''
def stderr(text):
    sys.stderr.write(text + '\n')


def error(text):
    stderr('Error: %s' % text)
    exit(-1)


def missarg(key):
    error('argument "%s" is required' % key)


def invarg(msg, arg):
    error('argument "%s" is wrong: %s' % (arg, msg))


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


def netmask_to_length(mask):
    return int(mask, 16).bit_count()


def ref(obj_id):
    return PyObj_FromPtr(obj_id)


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
