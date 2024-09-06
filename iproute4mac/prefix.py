import ipaddress

import iproute4mac.socket as socket


def version_to_family(version):
    if version == 4:
        return socket._AF_INET
    if version == 6:
        return socket._AF_INET6
    raise ValueError("unknown IP version")


def family_to_version(family):
    if family == socket._AF_INET:
        return 4
    if family == socket._AF_INET6:
        return 6
    raise ValueError("unknown address family")


class Prefix:
    __slots__ = ("_address", "_network", "_type")

    def __init__(self, prefix, family=None, version=None, pack=False):
        if family is not None and version is not None:
            raise ValueError("'family' and 'version' are mutually exclusive")
        elif family:
            version = family_to_version(family)
        elif version and version not in (4, 6):
            raise ValueError("unknown IP version")
        self._address = self._network = self._type = None
        if isinstance(prefix, ipaddress._IPAddressBase):
            if version and prefix.version != version:
                raise ValueError("prefix address family or version does not match")
            if isinstance(prefix, ipaddress._BaseAddress):
                self._address = prefix
                return
            if isinstance(prefix, ipaddress._BaseNetwork):
                if pack and prefix.prefixlen == prefix._max_prefixlen:
                    self._address = prefix.network_address
                else:
                    self._network = prefix
                return
        if not isinstance(prefix, str):
            raise ValueError(f"unsupported prefix type {type(prefix)}")
        if prefix == "localhost":
            if version == 4:
                self._address = ipaddress.ip_address("127.0.0.1")
            elif version == 6:
                self._address = ipaddress.ip_address("::1")
            else:
                self._type = "localhost"
            return
        if prefix == "any" or prefix == "all":
            if version == 4:
                self._address = ipaddress.ip_address("0.0.0.0")
            elif version == 6:
                self._address = ipaddress.ip_address("::")
            else:
                self._type = "any"
            return
        if prefix == "default":
            if version == 4:
                self._network = ipaddress.ip_network("0.0.0.0/0")
            elif version == 6:
                self._network = ipaddress.ip_network("::/0")
            else:
                self._type = "default"
            return
        if "/" in prefix:
            prefix, prefixlen = prefix.split("/")
        else:
            prefixlen = None
        if ":" not in prefix and (dots := prefix.count(".")) < 3:
            prefix += ".0" * (3 - dots)
            if not prefixlen:
                prefixlen = str((dots + 1) * 8)
        if prefixlen:
            try:
                self._network = ipaddress.ip_network(f"{prefix}/{prefixlen}")
            except ValueError:
                self._address = ipaddress.ip_address(prefix)
                self._network = ipaddress.ip_network(f"{prefix}/{prefixlen}", strict=False)
            if pack and self._network.prefixlen == self._network._max_prefixlen:
                self._address = self._network.network_address
                self._network = None
        else:
            self._address = ipaddress.ip_address(prefix)
        if version and self.address.version != version:
            raise ValueError("prefix address family or version does not match")

    def __eq__(self, other):
        if isinstance(other, str):
            other = Prefix(other)
        if isinstance(other, Prefix) and self._initialized and other._initialized:
            return self.prefix == other.prefix
        return str(self) == str(other)

    def __contains__(self, other):
        if not isinstance(other, str | Prefix):
            return False
        elif isinstance(other, str):
            other = Prefix(other)
        if self._is_default:
            return True
        if self._is_localhost:
            return other.is_localhost
        if self._is_any:
            return other.is_any
        if self._network:
            if not other._initialized:
                # NOTE: is "any" ["0.0.0.0"|"::"] a valid element inside a network?
                return Prefix(str(other), version=self.version) in self
            if self.version != other.version:
                return False
            if other.is_host:
                return other.address in self._network
            else:
                return other._network.subnet_of(self._network)
        if other._is_localhost:
            return self.is_localhost
        if other._is_any:
            return self.is_any
        # self._address
        if other.is_host:
            return other.address == self._address
        return False

    def __str__(self):
        if self.is_localhost:
            return "localhost"
        if self.is_any:
            return "any"
        if self.is_default:
            return "default"
        if self._type:
            return self.type
        if self._is_prefix:
            return str(self._address) + "/" + str(self._network.prefixlen)
        if self._address:
            return str(self._address)
        return str(self._network)

    def __repr__(self):
        if self._is_prefix:
            return str(self._address) + "/" + str(self._network.prefixlen)
        if self._address:
            return str(self._address)
        if self._network:
            return str(self._network)
        return self._type

    @property
    def _initialized(self):
        return bool(self._address) or bool(self._network)

    @property
    def _is_localhost(self):
        return self._type == "localhost"

    @property
    def _is_any(self):
        return self._type == "any"

    @property
    def _is_default(self):
        return self._type == "default"

    @property
    def _is_prefix(self):
        return bool(self._address) and bool(self._network)

    @property
    def _is_address(self):
        return bool(self._address) and not bool(self._network)

    @property
    def _is_network(self):
        return bool(self._network) and not bool(self._address)

    @property
    def is_localhost(self):
        if self._is_localhost:
            return True
        if self._address and not self._network:
            return str(self._address) in ["127.0.0.1", "::1"]
        return False

    @property
    def is_any(self):
        return self._is_any or (
            self._initialized and self.address._ip + self.prefixlen - self.max_prefixlen == 0
        )

    @property
    def is_default(self):
        return self._is_default or (self._initialized and self.address._ip + self.prefixlen == 0)

    @property
    def is_prefix(self):
        return self._is_prefix

    @property
    def is_network(self):
        return self._is_default or self._is_network

    @property
    def is_host(self):
        return (
            self._is_localhost
            or self._is_any
            or (self._initialized and self.prefixlen == self.max_prefixlen)
        )

    @property
    def is_link(self):
        if self._initialized:
            return self.address.is_link_local
        return False

    @property
    def is_global(self):
        if self._initialized:
            return self.address.is_global
        return self._is_default

    @property
    def address(self):
        if self._address:
            return self._address
        if self._network:
            return self._network.network_address
        return None

    @property
    def prefix(self):
        if self._type:
            return self._type
        if self._is_prefix:
            return str(self._address) + "/" + str(self._network.prefixlen)
        if self._address:
            return str(self._address) + "/" + str(self._address._max_prefixlen)
        return str(self._network)

    @property
    def prefixlen(self):
        if self._is_default:
            return 0
        if self._network:
            return self._network.prefixlen
        if self._address:
            return self._address._max_prefixlen
        raise ValueError("unknown prefix length")

    @property
    def max_prefixlen(self):
        if self._is_default:
            return 0
        if self._address:
            return self._address._max_prefixlen
        if self._network:
            return self._network._max_prefixlen
        raise ValueError("unknown prefix length")

    @property
    def version(self):
        if self._initialized:
            return self.address.version
        return 0

    @version.setter
    def version(self, value):
        if value not in (4, 6):
            raise ValueError(f'"{value}" does not appear to be a valid IP version protocol')
        if self._initialized:
            raise ValueError(
                "IP version protocol cannot be assigned to an already initialized prefix"
            )
        if self._is_localhost:
            if value == 4:
                self._address = ipaddress.ip_address("127.0.0.1")
            else:
                self._address = ipaddress.ip_address("::1")
        elif self._is_any:
            if value == 4:
                self._address = ipaddress.ip_address("0.0.0.0")
            else:
                self._address = ipaddress.ip_address("::")
        elif self._is_default:
            if value == 4:
                self._network = ipaddress.ip_network("0.0.0.0/0")
            else:
                self._network = ipaddress.ip_network("::/0")
        self._type = None

    @property
    def family(self):
        if self._initialized:
            return version_to_family(self.version)
        return 0

    @family.setter
    def family(self, value):
        self.version = family_to_version(value)
