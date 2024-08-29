VERSION = "0.4.1"

# socket.h
AF_UNSPEC = 0
AF_UNIX = 1
AF_INET = 2
AF_BRIDGE = 7
AF_INET6 = 10
AF_PACKET = 17  # not present in BSD
AF_MPLS = 28

ADDRESS_FAMILIES = [
    (AF_UNSPEC, "none"),
    (AF_INET, "inet"),
    (AF_INET6, "inet6"),
    (AF_PACKET, "link"),
    (AF_MPLS, "mpls"),
    (AF_BRIDGE, "bridge"),
]

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
    "uid": -1,
    "compress_vlans": False,
    "verbose": 2,
    "quiet": False,
}

# libc
EXIT_FAILURE = 1
EXIT_SUCCESS = 0
EXIT_ERROR = -1

# map operstates
OPER_STATES = {"active": "UP", "inactive": "DOWN"}

# MAC address RegEx
LLSEG = "[0-9a-fA-F]{1,2}"
LLADDR = "(?:%s(?::%s){5})" % (LLSEG, LLSEG)

# IPv4 RegEx
IPV4SEG = "(?:25[0-5]|2[0-4][0-9]|1{0,1}[0-9]{1,2})"
IPV4ADDR = r"(?:%s(?:\.%s){0,3})" % (IPV4SEG, IPV4SEG)
IPV4MASK = "(?:0x)?(?:[0-9a-fA-F]){8}"

# IPv6 RegEx
IPV6SEG = "(?:[0-9a-fA-F]{1,4})"
IPV6GROUPS = (
    "::",
    "(?:%s:){1,7}:" % (IPV6SEG),
    ":(?::%s){1,7}" % (IPV6SEG),
    "(?:%s:){1,6}:%s" % (IPV6SEG, IPV6SEG),
    "%s:(?::%s){1,6}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,5}(?::%s){1,2}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,4}(?::%s){1,3}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,3}(?::%s){1,4}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){1,2}(?::%s){1,5}" % (IPV6SEG, IPV6SEG),
    "(?:%s:){7,7}%s" % (IPV6SEG, IPV6SEG),
)
IPV6ADDR = "|".join([f"(?:{group})" for group in IPV6GROUPS[::-1]])
IPV6ADDR = f"(?:{IPV6ADDR})"

# ifconfig
IFNAME = r"(?:\w+\d+)"
NETIF = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
