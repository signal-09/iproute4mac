from socket import *

# Linux socket.h
_AF_UNSPEC = 0
_AF_UNIX = 1
_AF_INET = 2
_AF_BRIDGE = 7
_AF_INET6 = 10
_AF_PACKET = 17  # not present in BSD
_AF_MPLS = 28

ADDRESS_FAMILIES = [
    (_AF_UNSPEC, "none"),
    (_AF_INET, "inet"),
    (_AF_INET6, "inet6"),
    (_AF_PACKET, "link"),
    (_AF_MPLS, "mpls"),
    (_AF_BRIDGE, "bridge"),
]


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
