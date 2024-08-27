import iproute4mac.ifconfig as ifconfig

from iproute4mac.utils import *


# TODO: https://unix.stackexchange.com/questions/255484/how-can-i-bridge-two-interfaces-with-ip-iproute2


def explain():
    stderr("""\
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
    exit(-1)


def parse(argv, args):
    while argv:
        opt = argv.pop(0)
        if matches(opt, "forward_delay"):
            do_notimplemented(opt)
        elif matches(opt, "hello_time"):
            do_notimplemented(opt)
        elif matches(opt, "max_age"):
            do_notimplemented(opt)
        elif matches(opt, "ageing_time"):
            do_notimplemented(opt)
        elif matches(opt, "stp_state"):
            do_notimplemented(opt)
        elif matches(opt, "priority"):
            prio = next_arg(argv)
            try:
                assert 0 <= int(prio) <= 61440
            except (ValueError, AssertionError):
                invarg("Invalid priority", prio)
            args["priority"] = prio
        elif matches(opt, "vlan_filtering"):
            do_notimplemented(opt)
        elif matches(opt, "vlan_protocol"):
            do_notimplemented(opt)
        elif matches(opt, "group_fwd_mask"):
            do_notimplemented(opt)
        elif matches(opt, "group_address"):
            do_notimplemented(opt)
        elif matches(opt, "fdb_flush"):
            do_notimplemented(opt)
        elif matches(opt, "vlan_default_pvid"):
            do_notimplemented(opt)
        elif matches(opt, "vlan_stats_enabled"):
            do_notimplemented(opt)
        elif matches(opt, "vlan_stats_per_port"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_router"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_snooping"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_query_use_ifaddr"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_querier"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_hash_elasticity"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_hash_max"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_last_member_count"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_startup_query_count"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_last_member_interval"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_membership_interval"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_querier_interval"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_query_interval"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_query_response_interval"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_startup_query_interval"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_stats_enabled"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_igmp_version"):
            do_notimplemented(opt)
        elif matches(opt, "mcast_mld_version"):
            do_notimplemented(opt)
        elif matches(opt, "nf_call_iptables"):
            do_notimplemented(opt)
        elif matches(opt, "nf_call_ip6tables"):
            do_notimplemented(opt)
        elif matches(opt, "nf_call_arptables"):
            do_notimplemented(opt)
        elif matches(opt, "help"):
            explain()
        else:
            stderr(f'bridge: unknown command "{opt}"?')
            explain()


def add(dev, args):
    if res := ifconfig.run(dev, "create"):
        stdout(res, optional=True)


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
