import sys

from typing import Optional

from .ansi import isatty
from .prettier import env_bool


if sys.platform == "win32":  # pragma: no cover (windows)
    """Activate ANSI support on windows consoles.

    As of Windows 10, the windows conolse got some support for ANSI escape
    sequences. Unfortunately it has to be enabled first using `SetConsoleMode`.
    See: https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences

    Code snippet source: https://bugs.python.org/msg291732
    """
    import os
    import msvcrt
    import ctypes

    from ctypes import wintypes

    def _check_bool(result, func, args):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return args

    ERROR_INVALID_PARAMETER = 0x0057
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    LPDWORD = ctypes.POINTER(wintypes.DWORD)

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetConsoleMode.errcheck = _check_bool
    kernel32.GetConsoleMode.argtypes = (wintypes.HANDLE, LPDWORD)
    kernel32.SetConsoleMode.errcheck = _check_bool
    kernel32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)

    def _set_conout_mode(new_mode, mask=0xFFFFFFFF):
        # don't assume StandardOutput is a console.
        # open CONOUT$ instead
        fdout = os.open("CONOUT$", os.O_RDWR)
        try:
            hout = msvcrt.get_osfhandle(fdout)
            old_mode = wintypes.DWORD()
            kernel32.GetConsoleMode(hout, ctypes.byref(old_mode))
            mode = (new_mode & mask) | (old_mode.value & ~mask)
            kernel32.SetConsoleMode(hout, mode)
            return old_mode.value
        finally:
            os.close(fdout)

    def _enable_vt_mode():
        mode = mask = ENABLE_VIRTUAL_TERMINAL_PROCESSING
        try:
            return _set_conout_mode(mode, mask)
        except WindowsError as e:
            if e.winerror == ERROR_INVALID_PARAMETER:
                raise NotImplementedError
            raise

    try:
        _enable_vt_mode()
    except NotImplementedError:
        color_active = False
    else:
        color_active = True
else:  # pragma: win32 no cover
    color_active = True


def use_highlight(highlight: Optional[bool] = None, file_=None) -> bool:
    highlight = env_bool(highlight, 'PY_DEVTOOLS_HIGHLIGHT', None)

    if highlight is not None:
        return highlight

    return color_active and isatty(file_)
