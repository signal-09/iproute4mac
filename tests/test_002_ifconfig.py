import iproute4mac.ifconfig as ifconfig

from os import system
from subprocess import check_output


def shell(cmd):
    return check_output(cmd, shell=True).decode().rstrip()


def test_Ifconfig():
    links = ifconfig.Ifconfig()

    _LO0 = ifconfig.run(ifconfig._IFCONFIG_OPTS, "lo0")
    lo0 = links.lookup("interface", "lo0")
    assert str(lo0) == _LO0

    _EN0 = ifconfig.run(ifconfig._IFCONFIG_OPTS, "en0")
    en0 = links.lookup("interface", "en0")
    assert str(en0) == _EN0
