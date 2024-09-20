import json

import iproute4mac.ifconfig as ifconfig
import iproute4mac.libc as libc
import iproute4mac.utils as utils

from difflib import unified_diff

from iproute4mac import OPTION
from iproute4mac.utils import matches, strcmp, next_arg


def usage():
    utils.stderr("""\
Usage: ip debug { address | neigh | route }""")
    exit(libc.EXIT_ERROR)


def debug_address(argv=[]):
    utils.stdout('Testing "address":... ')

    old_options = utils.options_override({"show_details": True, "json": True, "pretty": True})
    interfaces = ifconfig.Ifconfig()
    utils.options_restore(old_options)
    ip_ifconfig = str(interfaces)
    os_ifconfig = ifconfig.run()

    ip_ifconfig_lines = [line.rstrip() for line in ip_ifconfig.splitlines()]
    os_ifconfig_lines = [line.rstrip() for line in os_ifconfig.splitlines()]

    if diff := list(
        unified_diff(
            ip_ifconfig_lines,
            os_ifconfig_lines,
            fromfile="ip address show",
            tofile=f"ifconfig {' '.join(ifconfig._IFCONFIG_OPTS)}",
            n=3 if OPTION["verbose"] <= 3 else 50,
        )
    ):
        utils.stdout(end="\n")
        utils.stdout("\n".join(list(diff)), end="\n")
    else:
        utils.stdout("OK", end="\n")

    return libc.EXIT_ERROR if len(diff) > 0 else libc.EXIT_SUCCESS


def debug_neigh(argv=[]):
    return libc.EXIT_SUCCESS


def debug_route(argv=[]):
    return libc.EXIT_SUCCESS


def all():
    err = debug_address()
    err += debug_neigh()
    err += debug_route()
    return libc.EXIT_ERROR if err else libc.EXIT_SUCCESS


def do_debug(argv):
    if not argv:
        return all()

    cmd = argv.pop(0)
    if matches(cmd, "address"):
        return debug_address(argv)
    elif matches(cmd, "neighbor", "neighbour"):
        return debug_neigh(argv)
    elif matches(cmd, "route"):
        return debug_route(argv)
    elif matches(cmd, "help"):
        return usage()

    utils.stderr(f'Command "{cmd}" is unknown, try "ip debug help".')
    exit(libc.EXIT_ERROR)
