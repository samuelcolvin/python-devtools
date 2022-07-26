import os
import sys

__all__ = (
    'isatty',
    'env_true',
    'env_bool',
    'use_highlight',
    'is_literal',
    'LaxMapping',
    'DataClassType',
    'SQLAlchemyClassType',
)

MYPY = False
if MYPY:
    from typing import Any, Optional, no_type_check
else:

    def no_type_check(x: 'Any') -> 'Any':
        return x


def isatty(stream: 'Any' = None) -> bool:
    stream = stream or sys.stdout
    try:
        return stream.isatty()
    except Exception:
        return False


def env_true(var_name: str, alt: 'Optional[bool]' = None) -> 'Any':
    env = os.getenv(var_name, None)
    if env:
        return env.upper() in {'1', 'TRUE'}
    else:
        return alt


def env_bool(value: 'Optional[bool]', env_name: str, env_default: 'Optional[bool]') -> 'Optional[bool]':
    if value is None:
        return env_true(env_name, env_default)
    else:
        return value


@no_type_check
def activate_win_color() -> bool:  # pragma: no cover
    """
    Activate ANSI support on windows consoles.

    As of Windows 10, the windows conolse got some support for ANSI escape
    sequences. Unfortunately it has to be enabled first using `SetConsoleMode`.
    See: https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences

    Code snippet source: https://bugs.python.org/msg291732
    """
    import ctypes
    import msvcrt
    import os
    from ctypes import wintypes

    def _check_bool(result, func, args):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return args

    ERROR_INVALID_PARAMETER = 0x0057
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    LPDWORD = ctypes.POINTER(wintypes.DWORD)

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.GetConsoleMode.errcheck = _check_bool
    kernel32.GetConsoleMode.argtypes = (wintypes.HANDLE, LPDWORD)
    kernel32.SetConsoleMode.errcheck = _check_bool
    kernel32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)

    def _set_conout_mode(new_mode, mask=0xFFFFFFFF):
        # don't assume StandardOutput is a console.
        # open CONOUT$ instead
        fdout = os.open('CONOUT$', os.O_RDWR)
        try:
            hout = msvcrt.get_osfhandle(fdout)
            old_mode = wintypes.DWORD()
            kernel32.GetConsoleMode(hout, ctypes.byref(old_mode))
            mode = (new_mode & mask) | (old_mode.value & ~mask)
            kernel32.SetConsoleMode(hout, mode)
            return old_mode.value
        finally:
            os.close(fdout)

    mode = mask = ENABLE_VIRTUAL_TERMINAL_PROCESSING
    try:
        _set_conout_mode(mode, mask)
    except WindowsError as e:  # type: ignore
        if e.winerror == ERROR_INVALID_PARAMETER:
            return False
        raise
    return True


def use_highlight(highlight: 'Optional[bool]' = None, file_: 'Any' = None) -> bool:
    highlight = env_bool(highlight, 'PY_DEVTOOLS_HIGHLIGHT', None)

    if highlight is not None:
        return highlight

    if sys.platform == 'win32':  # pragma: no cover
        return isatty(file_) and activate_win_color()
    return isatty(file_)


def is_literal(s: 'Any') -> bool:
    import ast

    try:
        ast.literal_eval(s)
    except (TypeError, MemoryError, SyntaxError, ValueError):
        return False
    else:
        return True


class MetaLaxMapping(type):
    def __instancecheck__(self, instance: 'Any') -> bool:
        return (
            hasattr(instance, '__getitem__')
            and hasattr(instance, 'items')
            and callable(instance.items)
            and type(instance) != type
        )


class LaxMapping(metaclass=MetaLaxMapping):
    pass


class MetaDataClassType(type):
    def __instancecheck__(self, instance: 'Any') -> bool:
        from dataclasses import is_dataclass

        return is_dataclass(instance)


class DataClassType(metaclass=MetaDataClassType):
    pass


class MetaSQLAlchemyClassType(type):
    def __instancecheck__(self, instance: 'Any') -> bool:
        try:
            from sqlalchemy.ext.declarative import DeclarativeMeta  # type: ignore
        except ImportError:
            return False
        else:
            return isinstance(instance.__class__, DeclarativeMeta)


class SQLAlchemyClassType(metaclass=MetaSQLAlchemyClassType):
    pass
