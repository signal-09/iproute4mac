import iproute4mac.ifconfig as ifconfig
import iproute4mac.libc as libc
import iproute4mac.utils as utils

from iproute4mac.utils import matches, strcmp, next_arg


# https://opensource.apple.com/source/xnu/xnu-7195.81.3/bsd/net/if_fake.c.auto.html
# https://apple.stackexchange.com/questions/337715/fake-ethernet-interfaces-feth-if-fake-anyone-ever-seen-this


def explain():
    utils.stderr("""\
Usage: ip link <options> type feth [peer <options>]
To get <options> type 'ip link add help""")
    exit(libc.EXIT_ERROR)


def parse(argv, args):
    while argv:
        opt = argv.pop(0)
        if strcmp(opt, "peer"):
            args["peer"] = next_arg(argv)
        else:
            utils.stderr(f'feth: unknown command "{opt}"?')
            explain()


def add(dev, args):
    peer = args.pop("peer", None)
    if res := ifconfig.run(dev, "create"):
        utils.stdout(res, end="\n", optional=True)
        dev = res.rstrip()

    try:
        if peer and (res := ifconfig.run(peer, "create", fatal=False)):
            peer = None
            assert isinstance(res, str)
            utils.stdout(res, end="\n", optional=True)
            peer = res.rstrip()
        if peer and (res := ifconfig.run(dev, "peer", peer, fatal=False)):
            assert isinstance(res, str)
    except AssertionError:
        if peer:
            ifconfig.run(peer, "destroy")
        ifconfig.run(dev, "destroy")
        exit(res)


def set(dev, args):
    pass


def delete(link, args):
    if peer := link.get("link", None):
        ifconfig.run(peer, "destroy")
    ifconfig.run(link["ifname"], "destroy")


def link(link, master):
    pass


def free(link, master):
    pass


def dump(argv, links):
    pass
