import ctypes
import ctypes.util


_libc = ctypes.CDLL(ctypes.util.find_library("c"))


def sysctl(name):
    size = ctypes.c_uint(0)
    _libc.sysctlbyname(name.encode(), None, ctypes.byref(size), None, 0)
    buf = ctypes.create_string_buffer(size.value)
    _libc.sysctlbyname(name.encode(), buf, ctypes.byref(size), None, 0)
    try:
        return buf.value.decode()
    except UnicodeError:
        return int.from_bytes(buf.raw, "little")
