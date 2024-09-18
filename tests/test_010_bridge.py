import iproute4mac
import iproute4mac.libc as libc

from iproute4mac.cmd.bridge import OBJS
from iproute4mac.utils import do_notimplemented


_CMD = "bridge"


def test_version(script_runner):
    for opt in ["--Version", "-Version", "-V"]:
        res = script_runner.run([_CMD, opt])
        assert res.returncode == libc.EXIT_SUCCESS
        assert res.stderr == ""
        assert res.stdout == f"{_CMD} wrapper, iproute4mac-{iproute4mac.__version__}\n"


def test_help(script_runner):
    for opt in ["help", "--help", "-help", "-h"]:
        res = script_runner.run([_CMD, opt])
        assert res.returncode == libc.EXIT_ERROR
        assert res.stderr.startswith(f"Usage: {_CMD}")
        assert res.stdout == ""


def test_obj_help(script_runner):
    for obj, func in OBJS:
        if obj == "help" or func == do_notimplemented:
            continue
        res = script_runner.run([_CMD, obj, "help"])
        assert res.returncode == libc.EXIT_ERROR
        assert res.stderr.startswith(f"Usage: {_CMD}")
        assert res.stdout == ""
