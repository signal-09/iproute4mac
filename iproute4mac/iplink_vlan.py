import iproute4mac.ifconfig as ifconfig

from iproute4mac.utils import *


LLPROTO_NAMES = (
    "loop",
    "pup",
    "pupat",
    "ip",
    "x25",
    "arp",
    "bpq",
    "ieeepup",
    "ieeepupat",
    "dec",
    "dna_dl",
    "dna_rc",
    "dna_rt",
    "lat",
    "diag",
    "cust",
    "sca",
    "rarp",
    "atalk",
    "aarp",
    "ipx",
    "ipv6",
    "ppp_disc",
    "ppp_ses",
    "atmmpoa",
    "atmfate",
    "802_3",
    "ax25",
    "all",
    "802_2",
    "snap",
    "ddcmp",
    "wan_ppp",
    "ppp_mp",
    "localtalk",
    "can",
    "ppptalk",
    "tr_802_2",
    "mobitex",
    "control",
    "irda",
    "econet",
    "tipc",
    "aoe",
    "802.1Q",
    "802.1ad",
    "mpls_uc",
    "mpls_mc",
    "teb",
    "LLDP",
    "ipv4",
)


def explain():
    stderr("""\
Usage: ... vlan id VLANID
               [ protocol VLANPROTO ]
               [ reorder_hdr { on | off } ]
               [ gvrp { on | off } ]
               [ mvrp { on | off } ]
               [ loose_binding { on | off } ]
               [ bridge_binding { on | off } ]
               [ ingress-qos-map QOS-MAP ]
               [ egress-qos-map QOS-MAP ]

VLANID := 0-4095
VLANPROTO: [ 802.1Q | 802.1ad ]
QOS-MAP := [ QOS-MAP ] QOS-MAPPING
QOS-MAPPING := FROM:TO""")
    exit(-1)


def parse(argv, args):
    while argv:
        opt = argv.pop(0)
        if matches(opt, "protocol"):
            proto = next_arg(argv)
            if not strcmp(proto, LLPROTO_NAMES):
                invarg("protocol is invalid", proto)
            do_notimplemented([opt])
        elif matches(opt, "id"):
            vlan_id = next_arg(argv)
            try:
                assert 0 <= int(vlan_id) < 2**12
            except (ValueError, AssertionError):
                invarg("id is invalid", vlan_id)
            args["id"] = vlan_id
        elif matches(opt, "reorder_hdr"):
            switch = next_arg(argv)
            if not strcmp(switch, "on", "off"):
                on_off("reorder_hdr", switch)
            do_notimplemented([opt])
        elif matches(opt, "gvrp"):
            switch = next_arg(argv)
            if not strcmp(switch, "on", "off"):
                on_off("gvrp", switch)
            do_notimplemented([opt])
        elif matches(opt, "mvrp"):
            switch = next_arg(argv)
            if not strcmp(switch, "on", "off"):
                on_off("mvrp", switch)
            do_notimplemented([opt])
        elif matches(opt, "loose_binding"):
            switch = next_arg(argv)
            if not strcmp(switch, "on", "off"):
                on_off("loose_binding", switch)
            do_notimplemented([opt])
        elif matches(opt, "bridge_binding"):
            switch = next_arg(argv)
            if not strcmp(switch, "on", "off"):
                on_off("bridge_binding", switch)
            do_notimplemented([opt])
        elif matches(opt, "ingress-qos-map"):
            do_notimplemented([opt])
        elif matches(opt, "egress-qos-map"):
            do_notimplemented([opt])
        elif matches(opt, "help"):
            explain()
        else:
            stderr(f'vlan: unknown command "{opt}"?')
            explain()


def add(dev, args):
    vlan_id = args.pop("id")
    vlan_link = args.pop("link")
    if res := ifconfig.exec(dev, "create"):
        stdout(res, optional=True)
        dev = res.rstrip()
    res = ifconfig.exec(dev, "vlan", vlan_id, "vlandev", vlan_link, fatal=False)
    if isinstance(res, int):
        res = ifconfig.exec(dev, "destroy")
    return res


def set(dev, args):
    return ""


def link(dev, master):
    pass


def free(dev, master):
    pass


def dump(argv, links):
    pass
