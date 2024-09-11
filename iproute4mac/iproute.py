import iproute4mac.data as data
import iproute4mac.libc as libc
import iproute4mac.prefix as prefix
import iproute4mac.route as route
import iproute4mac.socket as socket
import iproute4mac.utils as utils

from iproute4mac import OPTION
from iproute4mac.prefix import Prefix
from iproute4mac.utils import matches, strcmp, next_arg, get_addr, get_prefix


def usage():
    utils.stderr("""\
Usage: ip route { list | flush } SELECTOR
       ip route save SELECTOR
       ip route restore
       ip route showdump
       ip route get [ ROUTE_GET_FLAGS ] [ to ] ADDRESS
                            [ from ADDRESS iif STRING ]
                            [ oif STRING ] [ tos TOS ]
                            [ mark NUMBER ] [ vrf NAME ]
                            [ uid NUMBER ] [ ipproto PROTOCOL ]
                            [ sport NUMBER ] [ dport NUMBER ]
                            [ as ADDRESS ]
       ip route { add | del | change | append | replace } ROUTE
SELECTOR := [ root PREFIX ] [ match PREFIX ] [ exact PREFIX ]
            [ table TABLE_ID ] [ vrf NAME ] [ proto RTPROTO ]
            [ type TYPE ] [ scope SCOPE ]
ROUTE := NODE_SPEC [ INFO_SPEC ]
NODE_SPEC := [ TYPE ] PREFIX [ tos TOS ]
             [ table TABLE_ID ] [ proto RTPROTO ]
             [ scope SCOPE ] [ metric METRIC ]
             [ ttl-propagate { enabled | disabled } ]
INFO_SPEC := { NH | nhid ID } OPTIONS FLAGS [ nexthop NH ]...
NH := [ encap ENCAPTYPE ENCAPHDR ] [ via [ FAMILY ] ADDRESS ]
      [ dev STRING ] [ weight NUMBER ] NHFLAGS
FAMILY := [ inet | inet6 | mpls | bridge | link ]
OPTIONS := FLAGS [ mtu NUMBER ] [ advmss NUMBER ] [ as [ to ] ADDRESS ]
           [ rtt TIME ] [ rttvar TIME ] [ reordering NUMBER ]
           [ window NUMBER ] [ cwnd NUMBER ] [ initcwnd NUMBER ]
           [ ssthresh NUMBER ] [ realms REALM ] [ src ADDRESS ]
           [ rto_min TIME ] [ hoplimit NUMBER ] [ initrwnd NUMBER ]
           [ features FEATURES ] [ quickack BOOL ] [ congctl NAME ]
           [ pref PREF ] [ expires TIME ] [ fastopen_no_cookie BOOL ]
TYPE := { unicast | local | broadcast | multicast | throw |
          unreachable | prohibit | blackhole | nat }
TABLE_ID := [ local | main | default | all | NUMBER ]
SCOPE := [ host | link | global | NUMBER ]
NHFLAGS := [ onlink | pervasive ]
RTPROTO := [ kernel | boot | static | NUMBER ]
PREF := [ low | medium | high ]
TIME := NUMBER[s|ms]
BOOL := [1|0]
FEATURES := ecn
ENCAPTYPE := [ mpls | ip | ip6 | seg6 | seg6local | rpl | ioam6 | xfrm ]
ENCAPHDR := [ MPLSLABEL | SEG6HDR | SEG6LOCAL | IOAM6HDR | XFRMINFO ]
SEG6HDR := [ mode SEGMODE ] segs ADDR1,ADDRi,ADDRn [hmac HMACKEYID] [cleanup]
SEGMODE := [ encap | encap.red | inline | l2encap | l2encap.red ]
SEG6LOCAL := action ACTION [ OPTIONS ] [ count ]
ACTION := { End | End.X | End.T | End.DX2 | End.DX6 | End.DX4 |
            End.DT6 | End.DT4 | End.DT46 | End.B6 | End.B6.Encaps |
            End.BM | End.S | End.AS | End.AM | End.BPF }
OPTIONS := OPTION [ OPTIONS ]
OPTION := { flavors FLAVORS | srh SEG6HDR | nh4 ADDR | nh6 ADDR | iif DEV | oif DEV |
            table TABLEID | vrftable TABLEID | endpoint PROGNAME }
            table TABLEID | vrftable TABLEID | endpoint PROGNAME }
FLAVORS := { FLAVOR[,FLAVOR] }
FLAVOR := { psp | usp | usd | next-csid }
IOAM6HDR := trace prealloc type IOAM6_TRACE_TYPE ns IOAM6_NAMESPACE size IOAM6_TRACE_SIZE
XFRMINFO := if_id IF_ID [ link_dev LINK ]
ROUTE_GET_FLAGS := ROUTE_GET_FLAG [ ROUTE_GET_FLAGS ]
ROUTE_GET_FLAG := [ connected | fibmatch | notify ]""")
    exit(libc.EXIT_ERROR)


def iproute_add(argv):
    res = route.run("add", argv)
    if res.find("File exists") > -1:
        utils.stderr("RTNETLINK answers: File exists")
        exit(2)


def iproute_del(argv):
    res = route.run("delete", argv)
    if res.find("not in table") > -1:
        utils.stderr("RTNETLINK answers: No such process")
        exit(2)


def iproute_change(argv):
    route.run("change", argv)


def iproute_modify(cmd, argv):
    entry = {}
    modifiers = {}
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "src"):
            addr = get_addr(next_arg(argv), OPTION["preferred_family"])
            utils.do_notimplemented(addr)
        elif strcmp(opt, "as"):
            addr = next_arg(argv)
            if strcmp(addr, "to"):
                addr = next_arg(argv)
            addr = get_addr(addr, OPTION["preferred_family"])
            utils.do_notimplemented(addr)
        elif strcmp(opt, "via"):
            if "gateway" in entry:
                utils.invarg("use nexthop syntax to specify multiple via", opt)
            addr = argv.pop(0)
            family = socket.read_family(addr)
            if family == socket._AF_UNSPEC:
                family = OPTION["preferred_family"]
            else:
                addr = next_arg(argv)
            entry["gateway"] = get_addr(addr, family)
        elif strcmp(opt, "from"):
            addr = get_addr(next_arg(argv), OPTION["preferred_family"])
            utils.do_notimplemented(addr)
        elif strcmp(opt, "tos") or matches(opt, "dsfield"):
            tos = next_arg(argv)
            utils.do_notimplemented(tos)
        elif strcmp(opt, "expires"):
            expires = next_arg(argv)
            try:
                expires = int(expires)
                assert 0 <= expires < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"expires" value is invalid', expires)
            modifiers["expire"] = f"-expire {expires}"
        elif matches(opt, "metric", "priority") or strcmp(opt, "preference"):
            metric = next_arg(argv)
            try:
                metric = int(metric)
                assert 0 <= metric < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"metric" value is invalid', metric)
            utils.do_notimplemented(metric)
        elif strcmp(opt, "scope"):
            scope = next_arg(argv)
            utils.do_notimplemented(scope)
        elif strcmp(opt, "mtu"):
            mtu = next_arg(argv)
            if strcmp(mtu, "lock"):
                modifiers["mtu"] = "-lock -mtu "
                mtu = next_arg(argv)
            else:
                modifiers["mtu"] = "-mtu "
            try:
                assert 0 <= int(mtu) < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"mtu" value is invalid', mtu)
            modifiers["mtu"] += mtu
        elif strcmp(opt, "hoplimit"):
            hoplimit = next_arg(argv)
            if strcmp(hoplimit, "lock"):
                modifiers["hoplimit"] = "-lock -hopcount "
                hoplimit = next_arg(argv)
            else:
                modifiers["hoplimit"] = "-hopcount "
            try:
                assert 0 <= int(hoplimit) < 2**8
            except (ValueError, AssertionError):
                utils.invarg('"hoplimit" value is invalid', hoplimit)
            modifiers["hoplimit"] += hoplimit
        elif strcmp(opt, "advmss"):
            mss = next_arg(argv)
            if strcmp(mss, "lock"):
                mss = next_arg(argv)
            try:
                mss = int(mss)
                assert 0 <= mss < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"mss" value is invalid', mss)
            utils.do_notimplemented(mss)
        elif matches(opt, "reordering"):
            reord = next_arg(argv)
            if strcmp(reord, "lock"):
                reord = next_arg(argv)
            try:
                reord = int(reord)
                assert 0 <= reord < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"reordering" value is invalid', reord)
            utils.do_notimplemented(reord)
        elif strcmp(opt, "rtt"):
            rtt = next_arg(argv)
            if strcmp(rtt, "lock"):
                modifiers["rtt"] = "-lock -rtt "
                rtt = next_arg(argv)
            else:
                modifiers["rtt"] = "-rtt "
            try:
                assert 0 <= int(rtt) < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"rtt" value is invalid', rtt)
            modifiers["rtt"] += rtt
        elif strcmp(opt, "rto_min"):
            rto_min = next_arg(argv)
            try:
                rto_min = int(rto_min)
                assert 0 <= rto_min < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"rto_min" value is invalid', rto_min)
            utils.do_notimplemented(rto_min)
        elif matches(opt, "window", "cwnd", "initcwnd", "initrwnd"):
            win = next_arg(argv)
            if strcmp(win, "lock"):
                win = next_arg(argv)
            try:
                win = int(win)
                assert 0 <= win < 2**32
            except (ValueError, AssertionError):
                utils.invarg(f'"{opt}" value is invalid', win)
            utils.do_notimplemented(win)
        elif matches(opt, "features"):
            feature = next_arg(argv)
            utils.do_notimplemented(feature)
        elif matches(opt, "quickack"):
            quickack = next_arg(argv)
            try:
                quickack = int(quickack)
                assert 0 <= quickack <= 1
            except (ValueError, AssertionError):
                utils.invarg('"quickack" value should be 0 or 1', quickack)
            utils.do_notimplemented(quickack)
        elif matches(opt, "congctl"):
            rta = next_arg(argv)
            if strcmp(rta, "lock"):
                rta = next_arg(argv)
            utils.do_notimplemented(rta)
        elif matches(opt, "rttvar"):
            win = next_arg(argv)
            if strcmp(rtt, "lock"):
                modifiers["rttvar"] = "-lock -rttvar "
                win = next_arg(argv)
            else:
                modifiers["rttvar"] = "-rttvar "
            try:
                assert 0 <= int(win) < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"rttvar" value is invalid', win)
            modifiers["rttvar"] += win
        elif matches(opt, "ssthresh"):
            win = next_arg(argv)
            if strcmp(rtt, "lock"):
                modifiers["ssthresh"] = "-lock -ssthresh "
                win = next_arg(argv)
            else:
                modifiers["ssthresh"] = "-ssthresh "
            try:
                assert 0 <= int(win) < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"ssthresh" value is invalid', win)
            modifiers["ssthresh"] += win
        elif matches(opt, "realms"):
            realm = next_arg(argv)
            utils.do_notimplemented(realm)
        elif strcmp(opt, "onlink"):
            utils.do_notimplemented()
        elif strcmp(opt, "nexthop"):
            utils.do_notimplemented()
        elif strcmp(opt, "nhid"):
            nhid = next_arg(argv)
            try:
                nhid = int(nhid)
                assert 0 <= nhid < 2**32
            except (ValueError, AssertionError):
                utils.invarg('"id" value is invalid', nhid)
            utils.do_notimplemented(nhid)
        elif matches(opt, "protocol"):
            prot = next_arg(argv)
            utils.do_notimplemented(prot)
        elif matches(opt, "table"):
            tid = next_arg(argv)
            utils.do_notimplemented(tid)
        elif matches(opt, "vrf"):
            tid = next_arg(argv)
            utils.do_notimplemented(tid)
        elif strcmp(opt, "dev", "oif"):
            entry["dev"] = next_arg(argv)
        elif matches(opt, "pref"):
            pref = next_arg(argv)
            try:
                if not strcmp(pref, "low", "medium", "high"):
                    pref = int(pref)
                    assert 0 <= pref < 2**8
            except (ValueError, AssertionError):
                utils.invarg('"pref" value is invalid', pref)
            utils.do_notimplemented(pref)
        elif strcmp(opt, "encap"):
            encaptype = next_arg(argv)
            if not strcmp(
                encaptype,
                "mpls",
                "ip",
                "ip6",
                "ila",
                "bpf",
                "seg6",
                "seg6local",
                "rpl",
                "ioam6",
                "xfrm",
            ):
                utils.invarg('"encap type" value is invalid', encaptype)
            encaphdr = next_arg(argv)
            utils.do_notimplemented(encaphdr)
        elif strcmp(opt, "ttl-propagate"):
            ttl_prop = next_arg(argv)
            if not strcmp(ttl_prop, "enabled", "disabled"):
                utils.invarg('"ttl-propagate" value is invalid', ttl_prop)
            utils.do_notimplemented(ttl_prop)
        elif matches(opt, "fastopen_no_cookie"):
            fastopen_no_cookie = next_arg(argv)
            try:
                fastopen_no_cookie = int(fastopen_no_cookie)
                assert 0 <= fastopen_no_cookie <= 1
            except (ValueError, AssertionError):
                utils.invarg('"fastopen_no_cookie" value should be 0 or 1', fastopen_no_cookie)
            utils.do_notimplemented(fastopen_no_cookie)
        else:
            if strcmp(opt, "to"):
                opt = next_arg(argv)
            if route.is_rtn(opt):
                entry["rtn"] = route.get_rtn(opt)
                opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            entry["dst"] = get_prefix(opt, OPTION["preferred_family"])

    if "dst" not in entry:
        usage()

    if "gateway" in entry and entry["dst"].family == socket._AF_UNSPEC:
        entry["dst"].family = entry["gateway"].family

    for mod in modifiers:
        argv += modifiers[mod].split()

    if "dev" in entry:
        if "gateway" in entry:
            argv += f"-ifscope {entry['dev']} {entry['dst']} {entry['gateway']}".split()
        else:
            argv += f"{entry['dst']} -interface {entry['dev']}".split()
    else:
        if "gateway" in entry:
            argv += f"{entry['dst']} {entry['gateway']}".split()
        else:
            argv += f"{entry['dst']}".split()

    if "rtn" in entry:
        if entry["rtn"] == route._RTN_BLACKHOLE:
            if entry["dst"].family == socket._AF_INET:
                gw = "127.0.0.1"
            else:
                gw = "::1"
            argv += f"{gw} -blackhole".split()

    if matches(cmd, "add"):
        iproute_add(argv)
    elif matches(cmd, "delete"):
        iproute_del(argv)
    elif matches(cmd, "change"):
        iproute_change(argv)
    elif matches(cmd, "replace"):
        iproute_del(argv)
        iproute_add(argv)
    # elif matches(cmd, "prepend"):
    # elif matches(cmd, "append"):
    else:
        utils.do_notimplemented()

    return libc.EXIT_SUCCESS


def iproute_get(argv):
    to = None

    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "tos") or matches(opt, "dsfield"):
            tos = next_arg(argv)
            utils.do_notimplemented(tos)
        elif matches(opt, "from"):
            addr = next_arg(argv)
            if matches(addr, "help"):
                usage()
            utils.do_notimplemented(addr)
        elif matches(opt, "iif"):
            idev = next_arg(argv)
            utils.do_notimplemented(idev)
        elif matches(opt, "mark"):
            mark = next_arg(argv)
            utils.do_notimplemented(mark)
        elif matches(opt, "oif"):
            odev = next_arg(argv)
            utils.do_notimplemented(odev)
        elif matches(opt, "oif"):
            odev = next_arg(argv)
            utils.do_notimplemented(odev)
        elif matches(opt, "notify"):
            utils.do_notimplemented()
        elif matches(opt, "connected"):
            utils.do_notimplemented()
        elif matches(opt, "vrf"):
            odev = next_arg(argv)
            utils.do_notimplemented(odev)
        elif matches(opt, "uid"):
            uid = next_arg(argv)
            try:
                uid = int(uid)
                assert 0 <= uid < 2**32
            except (ValueError, AssertionError):
                utils.invarg("invalid UID", uid)
            OPTION["uid"] = uid
        elif matches(opt, "fibmatch"):
            utils.do_notimplemented()
        elif strcmp(opt, "as"):
            addr = next_arg(argv)
            if strcmp(addr, "to"):
                addr = next_arg(argv)
            addr = get_addr(addr, OPTION["preferred_family"])
            utils.do_notimplemented()
        elif matches(opt, "sport"):
            sport = next_arg(argv)
            try:
                sport = int(sport)
            except ValueError:
                utils.invarg("invalid sport", sport)
            utils.do_notimplemented(sport)
        elif matches(opt, "dport"):
            dport = next_arg(argv)
            try:
                dport = int(dport)
            except ValueError:
                utils.invarg("invalid dport", dport)
            utils.do_notimplemented(dport)
        elif matches(opt, "ipproto"):
            ipproto = next_arg(argv)
            try:
                ipproto = int(ipproto)
            except ValueError:
                utils.invarg('Invalid "ipproto" value', ipproto)
            utils.do_notimplemented(ipproto)
        else:
            if strcmp(opt, "to"):
                opt = next_arg(argv)
            if matches(opt, "help"):
                usage()
            to = get_prefix(opt, OPTION["preferred_family"])
            if "/" in str(to) and not to.is_host:
                utils.stderr(
                    "Warning: "
                    f"/{to.prefixlen} as prefix is invalid, "
                    f"only /{to.max_prefixlen} (or none) is supported."
                )
                to = Prefix(to.address)
            OPTION["preferred_family"] = to.family

    if not to:
        utils.stderr("need at least a destination address")
        return libc.EXIT_FAILURE

    utils.output(route.RouteGet(to, uid=OPTION["uid"]))

    return libc.EXIT_SUCCESS


def iproute_list(argv):
    if OPTION["preferred_family"] == socket._AF_UNSPEC:
        OPTION["preferred_family"] = socket._AF_INET

    entries = route.Routes()
    while argv:
        opt = argv.pop(0)
        if matches(opt, "table"):
            table = next_arg(argv)
            if strcmp(table, "help"):
                usage()
            elif strcmp(table, "all"):
                utils.hint('"table all" are simulated simply joining IPv4 and IPv6')
                OPTION["preferred_family"] = socket._AF_UNSPEC
            else:
                utils.do_notimplemented(opt)
        elif matches(opt, "vrf"):
            tid = next_arg(argv)
            utils.do_notimplemented(tid)
        elif matches(opt, "cached", "cloned"):
            utils.do_notimplemented()
        elif strcmp(opt, "tod") or matches(opt, "dsfield"):
            tos = next_arg(argv)
            utils.do_notimplemented(tos)
        elif matches(opt, "protocol"):
            protocol = next_arg(argv)
            if protocol not in ("static", "redirect", "kernel", "all"):
                utils.invarg('invalid "protocol"', protocol)
            if protocol == "all":
                continue
            entries.set([e for e in entries if e.get("protocol") == protocol])
            utils.delete_keys(entries, "protocol")
        elif matches(opt, "scope"):
            scope = next_arg(argv)
            if scope not in ("link", "host", "global", "all") and not scope.isdigit():
                utils.invarg('invalid "scope"', scope)
            if scope == "all":
                continue
            # FIXME: numeric scope?
            entries.set([e for e in entries if e.get("scope") == scope])
            utils.delete_keys(entries, "scope")
        elif matches(opt, "type"):
            rt = next_arg(argv)
            if not route.is_rtn(rt):
                utils.invarg("node type value is invalid", rt)
            entries.set(
                [
                    e
                    for e in entries
                    if (e.get("type") == rt or ("type" not in e and rt == "unicast"))
                ]
            )
        elif strcmp(opt, "dev", "oif", "iif"):
            dev = next_arg(argv)
            entries.set([e for e in entries if e.get("dev") == dev])
            data.delete_keys(entries, "dev")
        elif strcmp(opt, "mark"):
            mark = next_arg(argv)
            utils.do_notimplemented(mark)
        elif matches(opt, "metric", "priority") or strcmp(opt, "preference"):
            metric = next_arg(argv)
            try:
                metric = int(metric)
            except ValueError:
                utils.invarg('"metric" value is invalid', metric)
            utils.do_notimplemented()
        elif strcmp(opt, "via"):
            via = next_arg(argv)
            family = socket.read_family(via)
            if family == socket._AF_UNSPEC:
                family = OPTION["preferred_family"]
            else:
                via = next_arg(argv)
            via = get_prefix(via, family)
            entries.set([e for e in entries if e.present("gateway") and via in e["gateway"]])
            data.delete_keys(entries, "gateway")
        elif strcmp(opt, "src"):
            src = get_prefix(next_arg(argv), OPTION["preferred_family"])
            if not src._is_default:
                entries.set([e for e in entries if e.source_from(src)])
                if src.is_host:
                    data.delete_keys(entries, "prefsrc")
        elif matches(opt, "realms"):
            realm = next_arg(argv)
            utils.do_notimplemented(realm)
        elif matches(opt, "from"):
            opt = next_arg(argv)
            if matches(opt, "root"):
                opt = next_arg(argv)
                src = get_prefix(opt, OPTION["preferred_family"])
                utils.do_notimplemented()
            elif matches(opt, "match"):
                opt = next_arg(argv)
                src = get_prefix(opt, OPTION["preferred_family"])
                utils.do_notimplemented()
            else:
                if matches(opt, "exact"):
                    opt = next_arg(argv)
                src = get_prefix(opt, OPTION["preferred_family"])
                utils.do_notimplemented()
        else:
            if matches(opt, "to"):
                opt = next_arg(argv)
            if matches(opt, "root"):
                opt = next_arg(argv)
                to = get_prefix(opt, OPTION["preferred_family"])
                entries.set([e for e in entries if e.present("dst") and e["dst"] in to])
            elif matches(opt, "match"):
                opt = next_arg(argv)
                to = get_prefix(opt, OPTION["preferred_family"])
                entries.set([e for e in entries if e.present("dst") and to in e["dst"]])
            else:
                if matches(opt, "exact"):
                    opt = next_arg(argv)
                to = get_prefix(opt, OPTION["preferred_family"])
                entries.set([e for e in entries if e.present("dst") and to == e["dst"]])

    if OPTION["preferred_family"] != socket._AF_UNSPEC:
        entries.set([e for e in entries if e["dst"].family == OPTION["preferred_family"]])

    utils.output(entries)

    return libc.EXIT_SUCCESS


def do_iproute(argv):
    if not argv:
        return iproute_list(argv)

    cmd = argv.pop(0)
    if matches(cmd, "add", "change", "replace", "prepend", "append", "delete"):
        return iproute_modify(cmd, argv)
    elif matches(cmd, "test"):
        return utils.do_notimplemented()
    elif matches(cmd, "show", "lst", "list"):
        return iproute_list(argv)
    elif matches(cmd, "get"):
        return iproute_get(argv)
    elif matches(cmd, "flush"):
        return utils.do_notimplemented()
    elif matches(cmd, "save"):
        return utils.do_notimplemented()
    elif matches(cmd, "restore"):
        return utils.do_notimplemented()
    elif matches(cmd, "showdump"):
        return utils.do_notimplemented()
    elif matches(cmd, "help"):
        return usage()

    utils.stderr(f'Command "{cmd}" is unknown, try "ip route help".')
    exit(libc.EXIT_ERROR)
