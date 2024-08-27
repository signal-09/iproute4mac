import iproute4mac


_CMD = "ip"


def test_version(script_runner):
    for opt in ["--Version", "-Version", "-V"]:
        res = script_runner.run([_CMD, opt])
        assert res.returncode == iproute4mac.EXIT_SUCCESS
        assert res.stderr == ""
        assert res.stdout == f"{_CMD} wrapper, iproute4mac-{iproute4mac.VERSION}\n"


def test_help(script_runner):
    for opt in ["help", "--help", "-help", "-h"]:
        res = script_runner.run([_CMD, opt])
        assert res.returncode == iproute4mac.EXIT_ERROR
        assert res.stderr.startswith("Usage:")


def test_obj_help(script_runner):
    for obj in ["link", "address", "route", "neigh"]:
        res = script_runner.run([_CMD, obj, "help"])
        assert res.returncode == iproute4mac.EXIT_ERROR
        assert res.stderr.startswith(f"Usage: {_CMD} {obj}")
