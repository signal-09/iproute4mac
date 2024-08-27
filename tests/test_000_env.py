import pytest
import os


def test_uid():
    if os.getuid() != 0:
        pytest.exit("Root privileges required")
