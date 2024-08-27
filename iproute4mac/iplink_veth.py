import iproute4mac.iplink_feth as feth

from iproute4mac.utils import hint


def explain():
    hint("veth is not present in macOS, using feth instead")
    feth.explain()


def parse(argv, args):
    hint("veth is not present in macOS, using feth instead")
    feth.parse(argv, args)


def add(dev, args):
    feth.add(dev.replace("veth", "feth"), args)


def set(dev, args):
    feth.set(dev.replace("veth", "feth"), args)


def delete(link, args):
    feth.delete(link, args)


def link(link, master):
    feth.link(link, master)


def free(link, master):
    feth.free(link, master)


def dump(argv, links):
    feth.dump(argv, links)
