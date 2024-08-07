import ipaddress

from iproute4mac import *


class Prefix:
    __slots__ = ("_prefix", "_any")

    def __init__(self, prefix):
        if prefix == "default":
            self._prefix = None
            self._any = False
            return
        if prefix == "any":
            self._prefix = None
            self._any = True
            return
        self._any = False
        if "/" in prefix:
            prefix, prefixlen = prefix.split("/")
        else:
            prefixlen = None
        if ":" not in prefix and (dots := prefix.count(".")) < 3:
            prefix += ".0" * (3 - dots)
            if not prefixlen:
                prefixlen = str((dots + 1) * 8)
        if prefixlen:
            self._prefix = ipaddress.ip_network(f"{prefix}/{prefixlen}")
        else:
            self._prefix = ipaddress.ip_address(prefix)

    def __eq__(self, other):
        if self._prefix and other._prefix:
            return self.prefixlen == other.prefixlen and self.address == other.address
        if self._is_default and other.is_default:
            return True
        if other._is_default and self.is_default:
            return True
        return False

    def __contains__(self, other):
        if self._is_network:
            if other.is_host:
                return other.address in self._prefix
            else:
                return other._prefix.subnet_of(self._prefix)
        if other.is_host:
            return other.address == self._prefix
        if self._is_default and other.is_default:
            return True
        if other._is_default and self.is_default:
            return True
        return False

    def __str__(self):
        if self.is_default:
            return "default"
        if self.is_any:
            return "any"
        return str(self._prefix)

    def __repr__(self):
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
