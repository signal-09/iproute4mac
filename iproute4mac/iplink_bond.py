import iproute4mac.ifconfig as ifconfig
import iproute4mac.libc as libc
import iproute4mac.utils as utils

from iproute4mac.utils import matches, strcmp, next_arg


def explain():
    utils.stderr("""\
Usage: ... bond [ mode BONDMODE ] [ active_slave SLAVE_DEV ]
                [ clear_active_slave ] [ miimon MIIMON ]
                [ updelay UPDELAY ] [ downdelay DOWNDELAY ]
                [ peer_notify_delay DELAY ]
                [ use_carrier USE_CARRIER ]
                [ arp_interval ARP_INTERVAL ]
                [ arp_validate ARP_VALIDATE ]
                [ arp_all_targets ARP_ALL_TARGETS ]
                [ arp_ip_target [ ARP_IP_TARGET, ... ] ]
                [ primary SLAVE_DEV ]
                [ primary_reselect PRIMARY_RESELECT ]
                [ fail_over_mac FAIL_OVER_MAC ]
                [ xmit_hash_policy XMIT_HASH_POLICY ]
                [ resend_igmp RESEND_IGMP ]
                [ num_grat_arp|num_unsol_na NUM_GRAT_ARP|NUM_UNSOL_NA ]
                [ all_slaves_active ALL_SLAVES_ACTIVE ]
                [ min_links MIN_LINKS ]
                [ lp_interval LP_INTERVAL ]
                [ packets_per_slave PACKETS_PER_SLAVE ]
                [ tlb_dynamic_lb TLB_DYNAMIC_LB ]
                [ lacp_rate LACP_RATE ]
                [ lacp_active LACP_ACTIVE]
                [ ad_select AD_SELECT ]
                [ ad_user_port_key PORTKEY ]
                [ ad_actor_sys_prio SYSPRIO ]
                [ ad_actor_system LLADDR ]

BONDMODE := balance-rr|active-backup|balance-xor|broadcast|802.3ad|balance-tlb|balance-alb
ARP_VALIDATE := none|active|backup|all|filter|filter_active|filter_backup
ARP_ALL_TARGETS := any|all
PRIMARY_RESELECT := always|better|failure
FAIL_OVER_MAC := none|active|follow
XMIT_HASH_POLICY := layer2|layer2+3|layer3+4|encap2+3|encap3+4|vlan+srcmac
LACP_ACTIVE := off|on
LACP_RATE := slow|fast
AD_SELECT := stable|bandwidth|count""")
    exit(libc.EXIT_ERROR)


BOND_MODE = [
    ("balance-rr", None),
    ("active-backup", "static"),
    ("balance-xor", None),
    ("broadcast", None),
    ("802.3ad", "lacp"),
    ("balance-tlb", None),
    ("balance-alb", None),
]


def parse(argv, args):
    while argv:
        opt = argv.pop(0)
        if matches(opt, "mode"):
            bond = next_arg(argv)
            for linux_bond, bsd_bond in BOND_MODE:
                if strcmp(bond, linux_bond, bsd_bond):
                    break
            else:
                utils.invarg("invalid mode", bond)
            if not bsd_bond:
                utils.invarg("bond mode not supported", bond)
            args["mode"] = bsd_bond
        elif matches(opt, "active_slave"):
            utils.do_notimplemented(opt)
        elif matches(opt, "clear_active_slave"):
            utils.do_notimplemented(opt)
        elif matches(opt, "miimon"):
            utils.do_notimplemented(opt)
        elif matches(opt, "updelay"):
            utils.do_notimplemented(opt)
        elif matches(opt, "downdelay"):
            utils.do_notimplemented(opt)
        elif matches(opt, "peer_notify_delay"):
            utils.do_notimplemented(opt)
        elif matches(opt, "use_carrier"):
            utils.do_notimplemented(opt)
        elif matches(opt, "arp_interval"):
            utils.do_notimplemented(opt)
        elif matches(opt, "arp_ip_target"):
            utils.do_notimplemented(opt)
        elif matches(opt, "arp_validate"):
            utils.do_notimplemented(opt)
        elif matches(opt, "arp_all_targets"):
            utils.do_notimplemented(opt)
        elif matches(opt, "primary"):
            utils.do_notimplemented(opt)
        elif matches(opt, "primary_reselect"):
            utils.do_notimplemented(opt)
        elif matches(opt, "fail_over_mac"):
            utils.do_notimplemented(opt)
        elif matches(opt, "xmit_hash_policy"):
            utils.do_notimplemented(opt)
        elif matches(opt, "resend_igmp"):
            utils.do_notimplemented(opt)
        elif matches(opt, "num_grat_arp", "num_unsol_na"):
            utils.do_notimplemented(opt)
        elif matches(opt, "all_slaves_active"):
            utils.do_notimplemented(opt)
        elif matches(opt, "min_links"):
            utils.do_notimplemented(opt)
        elif matches(opt, "lp_interval"):
            utils.do_notimplemented(opt)
        elif matches(opt, "packets_per_slave"):
            utils.do_notimplemented(opt)
        elif matches(opt, "lacp_rate"):
            utils.do_notimplemented(opt)
        elif strcmp(opt, "lacp_active"):
            utils.do_notimplemented(opt)
        elif matches(opt, "ad_select"):
            utils.do_notimplemented(opt)
        elif matches(opt, "ad_user_port_key"):
            utils.do_notimplemented(opt)
        elif matches(opt, "ad_actor_sys_prio"):
            utils.do_notimplemented(opt)
        elif matches(opt, "ad_actor_system"):
            utils.do_notimplemented(opt)
        elif matches(opt, "tlb_dynamic_lb"):
            utils.do_notimplemented(opt)
        elif matches(opt, "help"):
            explain()
        else:
            utils.stderr(f'bond: unknown command "{opt}"?')
            explain()


def add(dev, args):
    if res := ifconfig.run(dev, "create"):
        utils.stdout(res, end="\n", optional=True)


def set(dev, args):
    res = ""
    for opt, value in args.items():
        if strcmp(opt, "mode"):
            res += ifconfig.run(dev, "bondmode", value)
    if res:
        utils.stdout(res, end="\n", optional=True)


def delete(link, args):
    ifconfig.run(link["ifname"], "destroy")


def link(link, master):
    ifconfig.run(master["ifname"], "bonddev", link["ifname"])


def free(link, master):
    ifconfig.run(master["ifname"], "-bonddev", link["ifname"])


def dump(argv, links):
    pass
