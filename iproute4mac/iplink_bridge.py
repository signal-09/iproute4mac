import iproute4mac.ifconfig as ifconfig
import iproute4mac.libc as libc
import iproute4mac.utils as utils

from iproute4mac.utils import matches, strcmp, next_arg


# TODO: https://unix.stackexchange.com/questions/255484/how-can-i-bridge-two-interfaces-with-ip-iproute2


def explain():
    utils.stderr("""\
Usage: ... bridge [ fdb_flush ]
                 [ forward_delay FORWARD_DELAY ]
                 [ hello_time HELLO_TIME ]
                 [ max_age MAX_AGE ]
                 [ ageing_time AGEING_TIME ]
                 [ stp_state STP_STATE ]
                 [ priority PRIORITY ]
                 [ group_fwd_mask MASK ]
                 [ group_address ADDRESS ]
                 [ vlan_filtering VLAN_FILTERING ]
                 [ vlan_protocol VLAN_PROTOCOL ]
                 [ vlan_default_pvid VLAN_DEFAULT_PVID ]
                 [ vlan_stats_enabled VLAN_STATS_ENABLED ]
                 [ vlan_stats_per_port VLAN_STATS_PER_PORT ]
                 [ mcast_snooping MULTICAST_SNOOPING ]
                 [ mcast_router MULTICAST_ROUTER ]
                 [ mcast_query_use_ifaddr MCAST_QUERY_USE_IFADDR ]
                 [ mcast_querier MULTICAST_QUERIER ]
                 [ mcast_hash_elasticity HASH_ELASTICITY ]
                 [ mcast_hash_max HASH_MAX ]
                 [ mcast_last_member_count LAST_MEMBER_COUNT ]
                 [ mcast_startup_query_count STARTUP_QUERY_COUNT ]
                 [ mcast_last_member_interval LAST_MEMBER_INTERVAL ]
                 [ mcast_membership_interval MEMBERSHIP_INTERVAL ]
                 [ mcast_querier_interval QUERIER_INTERVAL ]
                 [ mcast_query_interval QUERY_INTERVAL ]
                 [ mcast_query_response_interval QUERY_RESPONSE_INTERVAL ]
                 [ mcast_startup_query_interval STARTUP_QUERY_INTERVAL ]
                 [ mcast_stats_enabled MCAST_STATS_ENABLED ]
                 [ mcast_igmp_version IGMP_VERSION ]
                 [ mcast_mld_version MLD_VERSION ]
                 [ nf_call_iptables NF_CALL_IPTABLES ]
                 [ nf_call_ip6tables NF_CALL_IP6TABLES ]
                 [ nf_call_arptables NF_CALL_ARPTABLES ]

Where: VLAN_PROTOCOL := { 802.1Q | 802.1ad }""")
    exit(libc.EXIT_ERROR)


def parse(argv, args):
    while argv:
        opt = argv.pop(0)
        if matches(opt, "forward_delay"):
            utils.do_notimplemented(opt)
        elif matches(opt, "hello_time"):
            utils.do_notimplemented(opt)
        elif matches(opt, "max_age"):
            utils.do_notimplemented(opt)
        elif matches(opt, "ageing_time"):
            utils.do_notimplemented(opt)
        elif matches(opt, "stp_state"):
            utils.do_notimplemented(opt)
        elif matches(opt, "priority"):
            prio = next_arg(argv)
            try:
                assert 0 <= int(prio) <= 61440
            except (ValueError, AssertionError):
                utils.invarg("Invalid priority", prio)
            args["priority"] = prio
        elif matches(opt, "vlan_filtering"):
            utils.do_notimplemented(opt)
        elif matches(opt, "vlan_protocol"):
            utils.do_notimplemented(opt)
        elif matches(opt, "group_fwd_mask"):
            utils.do_notimplemented(opt)
        elif matches(opt, "group_address"):
            utils.do_notimplemented(opt)
        elif matches(opt, "fdb_flush"):
            utils.do_notimplemented(opt)
        elif matches(opt, "vlan_default_pvid"):
            utils.do_notimplemented(opt)
        elif matches(opt, "vlan_stats_enabled"):
            utils.do_notimplemented(opt)
        elif matches(opt, "vlan_stats_per_port"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_router"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_snooping"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_query_use_ifaddr"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_querier"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_hash_elasticity"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_hash_max"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_last_member_count"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_startup_query_count"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_last_member_interval"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_membership_interval"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_querier_interval"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_query_interval"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_query_response_interval"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_startup_query_interval"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_stats_enabled"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_igmp_version"):
            utils.do_notimplemented(opt)
        elif matches(opt, "mcast_mld_version"):
            utils.do_notimplemented(opt)
        elif matches(opt, "nf_call_iptables"):
            utils.do_notimplemented(opt)
        elif matches(opt, "nf_call_ip6tables"):
            utils.do_notimplemented(opt)
        elif matches(opt, "nf_call_arptables"):
            utils.do_notimplemented(opt)
        elif matches(opt, "help"):
            explain()
        else:
            utils.stderr(f'bridge: unknown command "{opt}"?')
            explain()


def add(dev, args):
    if res := ifconfig.run(dev, "create"):
        utils.stdout(res, end="\n", optional=True)


def set(dev, args):
    pass


def delete(link, args):
    ifconfig.run(link["ifname"], "destroy")


def link(link, master):
    ifconfig.run(master["ifname"], "addm", link["ifname"])


def free(link, master):
    ifconfig.run(master["ifname"], "deletem", link["ifname"])


def dump(argv, links):
    pass
