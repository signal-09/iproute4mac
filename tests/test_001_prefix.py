from iproute4mac.prefix import Prefix


def test_localhost():
    addresses = (
        (Prefix("localhost"), True),
        (Prefix("any"), False),
        (Prefix("default"), False),
        (Prefix("localhost", version=4), True),
        (Prefix("any", version=4), False),
        (Prefix("default", version=4), False),
        (Prefix("localhost", version=6), True),
        (Prefix("any", version=6), False),
        (Prefix("default", version=6), False),
        (Prefix("172.16"), False),
        (Prefix("172.16.19"), False),
        (Prefix("172.16.19.74"), False),
        (Prefix("10.0.0.0/8"), False),
        (Prefix("10.0.0.1"), False),
        (Prefix("10.0.0.2/24"), False),
        (Prefix("10.0.0.3/32"), False),
        (Prefix("23ff:fc1b::/32"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/64"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/128"), False),
    )
    for a, v in addresses:
        print(repr(a))
        assert a.is_localhost == v


def test_any():
    addresses = (
        (Prefix("localhost"), False),
        (Prefix("any"), True),
        (Prefix("default"), False),
        (Prefix("localhost", version=4), False),
        (Prefix("any", version=4), True),
        (Prefix("default", version=4), False),
        (Prefix("localhost", version=6), False),
        (Prefix("any", version=6), True),
        (Prefix("default", version=6), False),
        (Prefix("172.16"), False),
        (Prefix("172.16.19"), False),
        (Prefix("172.16.19.74"), False),
        (Prefix("10.0.0.0/8"), False),
        (Prefix("10.0.0.1"), False),
        (Prefix("10.0.0.2/24"), False),
        (Prefix("10.0.0.3/32"), False),
        (Prefix("23ff:fc1b::/32"), False),
        (Prefix("23ff:fc1b::/64"), False),
        (Prefix("23ff:fc1b::/128"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/64"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/128"), False),
    )
    for a, v in addresses:
        print(repr(a))
        assert a.is_any == v


def test_default():
    addresses = (
        (Prefix("localhost"), False),
        (Prefix("any"), False),
        (Prefix("default"), True),
        (Prefix("localhost", version=4), False),
        (Prefix("any", version=4), False),
        (Prefix("default", version=4), True),
        (Prefix("localhost", version=6), False),
        (Prefix("any", version=6), False),
        (Prefix("default", version=6), True),
        (Prefix("172.16"), False),
        (Prefix("172.16.19"), False),
        (Prefix("172.16.19.74"), False),
        (Prefix("10.0.0.0/8"), False),
        (Prefix("10.0.0.1"), False),
        (Prefix("10.0.0.2/24"), False),
        (Prefix("10.0.0.3/32"), False),
        (Prefix("23ff:fc1b::/32"), False),
        (Prefix("23ff:fc1b::/64"), False),
        (Prefix("23ff:fc1b::/128"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/64"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/128"), False),
    )
    for a, v in addresses:
        print(repr(a))
        assert a.is_default == v


def test_prefix():
    addresses = (
        (Prefix("localhost"), False),
        (Prefix("any"), False),
        (Prefix("default"), False),
        (Prefix("localhost", version=4), False),
        (Prefix("any", version=4), False),
        (Prefix("default", version=4), False),
        (Prefix("localhost", version=6), False),
        (Prefix("any", version=6), False),
        (Prefix("default", version=6), False),
        (Prefix("172.16"), False),
        (Prefix("172.16.19"), False),
        (Prefix("172.16.19.74"), False),
        (Prefix("10.0.0.0/8"), False),
        (Prefix("10.0.0.1"), False),
        (Prefix("10.0.0.2/24"), True),
        (Prefix("10.0.0.3/32"), False),
        (Prefix("23ff:fc1b::/32"), False),
        (Prefix("23ff:fc1b::/64"), False),
        (Prefix("23ff:fc1b::/128"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/64"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c/128"), False),
    )
    for a, v in addresses:
        print(repr(a))
        assert a.is_prefix == v


def test_network():
    addresses = (
        (Prefix("localhost"), False),
        (Prefix("any"), False),
        (Prefix("default"), True),
        (Prefix("localhost", version=4), False),
        (Prefix("any", version=4), False),
        (Prefix("default", version=4), True),
        (Prefix("localhost", version=6), False),
        (Prefix("any", version=6), False),
        (Prefix("default", version=6), True),
        (Prefix("172.16"), True),
        (Prefix("172.16.19"), True),
        (Prefix("172.16.19.74"), False),
        (Prefix("10.0.0.0/8"), True),
        (Prefix("10.0.0.1"), False),
        (Prefix("10.0.0.2/24"), False),
        (Prefix("10.0.0.3/32"), True),
        (Prefix("23ff:fc1b::/32"), True),
        (Prefix("23ff:fc1b::/64"), True),
        (Prefix("23ff:fc1b::/128"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/64"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/128"), True),
    )
    for a, v in addresses:
        print(repr(a))
        assert a.is_network == v


def test_host():
    addresses = (
        (Prefix("localhost"), True),
        (Prefix("any"), True),
        (Prefix("default"), False),
        (Prefix("localhost", version=4), True),
        (Prefix("any", version=4), True),
        (Prefix("default", version=4), False),
        (Prefix("localhost", version=6), True),
        (Prefix("any", version=6), True),
        (Prefix("default", version=6), False),
        (Prefix("172.16"), False),
        (Prefix("172.16.19"), False),
        (Prefix("172.16.19.74"), True),
        (Prefix("10.0.0.0/8"), False),
        (Prefix("10.0.0.1"), True),
        (Prefix("10.0.0.2/24"), False),
        (Prefix("10.0.0.3/32"), True),
        (Prefix("23ff:fc1b::/32"), False),
        (Prefix("23ff:fc1b::/64"), False),
        (Prefix("23ff:fc1b::/128"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c/64"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c/128"), True),
    )
    for a, v in addresses:
        print(repr(a))
        assert a.is_host == v


def test_eq():
    addresses = (
        (Prefix("0.0.0.0"), Prefix("0.0.0.0/32"), True),
        (Prefix("0.0.0.0"), Prefix("::"), False),
        (Prefix("0.0.0.0"), Prefix("any"), True),
        (Prefix("0.0.0.0"), Prefix("any", version=4), True),
        (Prefix("0.0.0.0/0"), Prefix("::/0"), False),
        (Prefix("0.0.0.0/0"), Prefix("default"), True),
        (Prefix("0.0.0.0/0"), Prefix("default", version=4), True),
        (Prefix("0.0.0.0/32"), Prefix("0.0.0.0"), True),
        (Prefix("127.0.0.1"), Prefix("localhost"), True),
        (Prefix("192.168.0.1"), Prefix("192.168.0.1/24"), False),
        (Prefix("192.168.0.1"), Prefix("192.168.0.1/32"), True),
        (Prefix("192.168.0.1/24"), Prefix("192.168.0.1"), False),
        (Prefix("192.168.0.1/32"), Prefix("192.168.0.1"), True),
        (Prefix("::"), Prefix("0.0.0.0"), False),
        (Prefix("::"), Prefix("any"), True),
        (Prefix("::/0"), Prefix("0.0.0.0/0"), False),
        (Prefix("::/0"), Prefix("default"), True),
        (Prefix("::1"), Prefix("localhost"), True),
        (Prefix("any"), Prefix("0.0.0.0"), True),
        (Prefix("any"), Prefix("::"), True),
        (Prefix("default"), Prefix("0.0.0.0/0"), True),
        (Prefix("default"), Prefix("::/0"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), Prefix("fe80::f03c:92ff:fe55:e32c/128"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c/128"), Prefix("fe80::f03c:92ff:fe55:e32c"), True),
        (Prefix("localhost"), Prefix("127.0.0.1"), True),
        (Prefix("localhost"), Prefix("::1"), True),
    )
    for a, b, v in addresses:
        print(repr(a), repr(b))
        assert (a == b) == v


def test_in():
    addresses = (
        (Prefix("0.0.0.0"), Prefix("::"), False),
        (Prefix("0.0.0.0"), Prefix("any"), True),
        (Prefix("0.0.0.0"), Prefix("any", version=4), True),
        (Prefix("0.0.0.0/0"), Prefix("::/0"), False),
        (Prefix("0.0.0.0/0"), Prefix("any"), False),
        (Prefix("0.0.0.0/0"), Prefix("default"), True),
        (Prefix("0.0.0.0/0"), Prefix("default", version=4), True),
        (Prefix("0.0.0.0/0"), Prefix("localhost"), False),
        (Prefix("127.0.0.1"), Prefix("::1"), False),
        (Prefix("127.0.0.1"), Prefix("localhost"), True),
        (Prefix("192.168.0.1"), Prefix("192.168.0.1/24"), True),
        (Prefix("192.168.0.1"), Prefix("192.168.0.1/32"), True),
        (Prefix("192.168.0.1/24"), Prefix("192.168.0.1"), False),
        (Prefix("192.168.0.1/32"), Prefix("192.168.0.1"), True),
        (Prefix("::"), Prefix("0.0.0.0"), False),
        (Prefix("::"), Prefix("any"), True),
        (Prefix("::/0"), Prefix("0.0.0.0/0"), False),
        (Prefix("::/0"), Prefix("any"), False),
        (Prefix("::/0"), Prefix("default"), True),
        (Prefix("::/0"), Prefix("localhost"), False),
        (Prefix("::1"), Prefix("127.0.0.1"), False),
        (Prefix("::1"), Prefix("localhost"), True),
        (Prefix("any"), Prefix("0.0.0.0"), True),
        (Prefix("any"), Prefix("0.0.0.0/0"), True),
        (Prefix("any"), Prefix("::"), True),
        (Prefix("any"), Prefix("::/0"), True),
        (Prefix("any"), Prefix("any"), True),
        (Prefix("any"), Prefix("default"), True),
        (Prefix("any"), Prefix("localhost"), False),
        (Prefix("default"), Prefix("0.0.0.0/0"), True),
        (Prefix("default"), Prefix("::/0"), True),
        (Prefix("default"), Prefix("any"), False),
        (Prefix("default"), Prefix("default"), True),
        (Prefix("default"), Prefix("localhost"), False),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), Prefix("fe80::f03c:92ff:fe55:e32c/128"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c"), Prefix("fe80::f03c:92ff:fe55:e32c/64"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c/128"), Prefix("fe80::f03c:92ff:fe55:e32c"), True),
        (Prefix("fe80::f03c:92ff:fe55:e32c/64"), Prefix("fe80::f03c:92ff:fe55:e32c"), False),
        (Prefix("localhost"), Prefix("0.0.0.0/0"), True),
        (Prefix("localhost"), Prefix("127.0.0.1"), True),
        (Prefix("localhost"), Prefix("::/0"), True),
        (Prefix("localhost"), Prefix("::1"), True),
        (Prefix("localhost"), Prefix("default"), True),
        (Prefix("localhost"), Prefix("any"), False),
        (Prefix("localhost"), Prefix("localhost"), True),
    )
    for a, b, v in addresses:
        print(repr(a), repr(b))
        assert (a in b) == v


def test_pack():
    addresses = (
        (Prefix("192.168.0.1/24", pack=True), "192.168.0.1/24"),
        (Prefix("192.168.0.1/32", pack=True), "192.168.0.1"),
        (Prefix("192.168.0.0/32", pack=True), "192.168.0.0"),
        (Prefix("192.168.0.1/24", pack=False), "192.168.0.1/24"),
        (Prefix("192.168.0.1/32", pack=False), "192.168.0.1/32"),
        (Prefix("192.168.0.0/32", pack=False), "192.168.0.0/32"),
    )
    for a, b in addresses:
        print(repr(a), b)
        assert repr(a) == b
