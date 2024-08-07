import json
import os
import re
import socket
import subprocess
import sys

from _ctypes import PyObj_FromPtr

from iproute4mac import *
from iproute4mac.prefix import Prefix


# global options
OPTION = {
    "preferred_family": AF_UNSPEC,
    "human_readable": False,
    "use_iec": False,
    "show_stats": False,
    "show_details": False,
    "oneline": False,
    "brief": False,
    "json": False,
    "pretty": False,
    "timestamp": False,
    "timestamp_short": False,
    "echo_request": False,
    "force": False,
    "max_flush_loops": 10,
    "batch_mode": False,
    "do_all": False,
    "uid": os.getuid(),
    "compress_vlans": False,
    "verbose": 2,
    "quiet": False,
}

# logging
LOG_STDERR = 0
LOG_HINT = 1
LOG_ERROR = 2
LOG_WARN = 3
LOG_INFO = 4
LOG_DEBUG = 5
LOG_LABEL = (None, "Hint", "Error", "Warning", "Info", "Debug")


def stdout(*argv, sep="", end="", optional=False):
    if optional and OPTION["quiet"]:
        return
    print(*argv, sep=sep, end=end)


def stderr(text, log_level=LOG_STDERR):
    if OPTION["verbose"] < log_level or not text:
        return
    if log_level > LOG_STDERR:
        text = LOG_LABEL[log_level] + ": " + text
    sys.stderr.write(text.rstrip() + "\n")


def error(text):
    stderr(text, log_level=LOG_ERROR)
    exit(-1)


def warn(text):
    stderr(text, log_level=LOG_WARN)


def info(text):
    stderr(text, log_level=LOG_INFO)


def debug(text):
    stderr(text, log_level=LOG_DEBUG)


def hint(text):
    stderr(text, log_level=LOG_HINT)


def missarg(key):
    error(f'argument "{key}" is required')


def invarg(msg, arg):
    error(f'argument "{arg}" is wrong: {msg}')


def duparg(key, arg):
    error(f'duplicate "{key}": "{arg}" is the second value.')


def duparg2(key, arg):
    error(f'either "{key}" is duplicate, or "{arg}" is a garbage.')


def on_off(msg, arg):
    error(f'argument of "{msg}" must be "on" or "off", not "{arg}"')


def on_off_switch(key, arg):
    return key if arg == "on" else f"-{key}"


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
        return json.dumps(data, cls=PrettyJSON, indent=4)
    return json.dumps(data, cls=SimpleJSON, separators=(",", ":"))


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


class SimpleJSON(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Prefix):
            return str(obj)
        return super(SimpleJSON, self).default(obj)


class PrettyJSON(json.JSONEncoder):
    FORMAT_SPEC = "@@{}@@"
    regex = re.compile(FORMAT_SPEC.format(r"(\d+)"))

    def default(self, obj):
        if isinstance(obj, NoIndent):
            return self.FORMAT_SPEC.format(id(obj))
        if isinstance(obj, Prefix):
            return str(obj)
        return super(PrettyJSON, self).default(obj)

    def encode(self, obj):
        obj = json_unindent_list(obj)
        format_spec = self.FORMAT_SPEC
        json_repr = super(PrettyJSON, self).encode(obj)
        for match in self.regex.finditer(json_repr):
            id = int(match.group(1))
            json_repr = json_repr.replace(f'"{format_spec.format(id)}"', repr(ref(id)))
        json_repr = re.sub(r"\[\n\s+{", "[ {", json_repr)
        json_repr = re.sub(r"},\n\s+{", "},{", json_repr)
        json_repr = re.sub(r"}\n\s*\]", "} ]", json_repr)
        return json_repr


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


def strcmp(opt, *argv):
    args = flat_touple(*argv)
    return any(arg == opt for arg in args)


def matches(opt, *argv):
    args = flat_touple(*argv)
    return any(arg.startswith(opt) for arg in args)


def startwith(opt, *argv):
    args = flat_touple(*argv)
    return any(opt.startswith(arg) for arg in args)


def endwith(opt, *argv):
    args = flat_touple(*argv)
    return any(opt.endswith(arg) for arg in args)


def matches_color(opt):
    if "=" in opt:
        (opt, arg) = opt.split("=", 1)
    else:
        arg = "always"
    return "-color".startswith(opt) and arg in ["always", "auto", "never"]


def check_dict(source, field, value):
    return field in source and source[field] == value


def list_index(source, field, value):
    return next((index for (index, element) in enumerate(source) if element[field] == value), -1)


def deep_update(source, update):
    for key, value in update.items():
        if isinstance(value, dict) and key in source:
            deep_update(source[key], value)
            continue
        source[key] = value


def do_notimplemented(argv=[]):
    if argv:
        error('"' + " ".join(argv) + '" not implemented')
    else:
        error("function not implemented")


def shell(*argv, fatal=True, hidden=False):
    args = flat_touple(*argv)
    info('executing "' + " ".join(args) + '"')
    cmd = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    if cmd.returncode != 0:
        stderr(cmd.stderr)
        if fatal:
            exit(cmd.returncode)
        else:
            return cmd.returncode
    else:
        warn(cmd.stderr)
        if cmd.stdout:
            debug(f"STDOUT\n{cmd.stdout}^^^ STDOUT ^^^")
    return cmd.stdout


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
