import json
import os
import re
import socket
import subprocess
import sys

from _ctypes import PyObj_FromPtr

from iproute4mac import *
from iproute4mac.prefix import Prefix


# logging
LOG_STDERR = 0
LOG_HINT = 1
LOG_ERROR = 2
LOG_WARN = 3
LOG_INFO = 4
LOG_DEBUG = 5
LOG_LABEL = (None, "Hint", "Error", "Warning", "Info", "Debug")

OPTION["uid"] = os.getuid()


def stdout(*args, sep="", end="", optional=False):
    if optional and OPTION["quiet"]:
        return
    print(*args, sep=sep, end=end)


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


def output(obj):
    if OPTION["json"]:
        stdout(json_dumps(obj.dict(details=OPTION["show_details"])), end="\n")
    else:
        stdout(obj.str(details=OPTION["show_details"]))


def next_arg(argv):
    try:
        return argv.pop(0)
    except IndexError:
        incomplete_command()


def read_family(name):
    for f, n in ADDRESS_FAMILIES:
        if name == n:
            return f
    return AF_UNSPEC


def family_name(family):
    for f, n in ADDRESS_FAMILIES:
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


def json_dumps(data):
    if OPTION["pretty"]:
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


def flat_tuple(*args):
    res = ()
    for arg in args:
        if arg is None:
            continue
        if isinstance(arg, list | tuple):
            res += flat_tuple(*arg)
        else:
            res += (str(arg),)
    return res


def strcmp(opt, *args):
    return any(arg == opt for arg in flat_tuple(*args))


def matches(opt, *args):
    return any(arg.startswith(opt) for arg in flat_tuple(*args))


def startwith(opt, *args):
    return any(opt.startswith(arg) for arg in flat_tuple(*args))


def endwith(opt, *args):
    return any(opt.endswith(arg) for arg in flat_tuple(*args))


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


def options_override(options={}):
    for key, value in options.items():
        OPTION[key], options[key] = value, OPTION[key]
    return options


def options_restore(options={}):
    OPTION.update(options)


def shell(*args, fatal=True):
    args = flat_tuple(*args)
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
    addr = Prefix(name, family=family)
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


def get_prefsrc(host):
    sock = socket.socket(host.family, socket.SOCK_DGRAM)
    sock.connect((repr(host), 7))
    src = sock.getsockname()[0]
    sock.close()
    return src


def do_notsupported(*args):
    if args:
        error('"' + " ".join(map(str, args)) + '" not supported')
    else:
        error("function not supported")


def do_notimplemented(*args):
    if args:
        error('"' + " ".join(map(str, args)) + '" not implemented')
    else:
        error("function not implemented")
