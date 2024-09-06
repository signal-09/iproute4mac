import ctypes
import ctypes.util


_LIBC = ctypes.CDLL(ctypes.util.find_library("c"))

EXIT_FAILURE = 1
EXIT_SUCCESS = 0
EXIT_ERROR = 255


def sysctl(name):
    size = ctypes.c_uint(0)
    _LIBC.sysctlbyname(name.encode(), None, ctypes.byref(size), None, 0)
    buf = ctypes.create_string_buffer(size.value)
    _LIBC.sysctlbyname(name.encode(), buf, ctypes.byref(size), None, 0)
    try:
        return buf.value.decode()
    except UnicodeError:
        # FIXME: catch struct output
        return int.from_bytes(buf.raw, "little")
