from pbr.version import VersionInfo


version_info = VersionInfo("iproute4mac")
__version__ = version_info.release_string()

# global options
OPTION = {
    "preferred_family": 0,
    "human_readable": False,
    "use_iec": False,
    "show_stats": False,
    "show_details": False,
    "oneline": False,
    "brief": False,
    "json": False,
    "pretty": False,
    "timestamp": False,
    "timestamp_short": False,
    "echo_request": False,
    "force": False,
    "max_flush_loops": 10,
    "batch_mode": False,
    "do_all": False,
    "uid": -1,
    "compress_vlans": False,
    "verbose": 3,
}
