import iproute4mac.ifconfig as ifconfig


def test_Ifconfig():
    links = ifconfig.Ifconfig()
    interfaces = links.list()
    for interface in interfaces:
        ifc = links.ifconfig(interface)
        ipr = links.iproute2(interface)
        assert ipr["ifindex"] == ifc["index"]
        assert ipr["ifname"] == ifc["interface"]
        assert ipr["flags"] == ifc["flags"]
        assert ipr["mtu"] == ifc["mtu"]
