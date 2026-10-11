import os
import sys
from typing import Any

__all__ = (
    'DataClassType',
    'LaxMapping',
    'SQLAlchemyClassType',
    'env_bool',
    'env_true',
    'is_literal',
    'isatty',
    'use_highlight',
)


def isatty(stream: Any = None) -> bool:
    stream = stream or sys.stdout
    try:
        return stream.isatty()
    except Exception:
        return False


def env_true(var_name: str, alt: bool | None = None) -> Any:
    env = os.getenv(var_name, None)
    if env:
        return env.upper() in {'1', 'TRUE'}
    else:
        return alt


def env_bool(value: bool | None, env_name: str, env_default: bool | None) -> bool | None:
    if value is None:
        return env_true(env_name, env_default)
    else:
        return value


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

    def _check_bool(result: Any, func: Any, args: Any) -> Any:
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

    def _set_conout_mode(new_mode: int, mask: int = 0xFFFFFFFF) -> int:
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
    except OSError as e:
        if e.winerror == ERROR_INVALID_PARAMETER:
            return False
        raise
    return True


def use_highlight(highlight: bool | None = None, file_: Any = None) -> bool:
    highlight = env_bool(highlight, 'PY_DEVTOOLS_HIGHLIGHT', None)

    if highlight is not None:
        return highlight

    if sys.platform == 'win32':  # pragma: no cover
        return isatty(file_) and activate_win_color()
    return isatty(file_)


def is_literal(s: Any) -> bool:
    import ast

    try:
        ast.literal_eval(s)
    except (TypeError, MemoryError, SyntaxError, ValueError):
        return False
    else:
        return True


class MetaLaxMapping(type):
    def __instancecheck__(self, instance: Any) -> bool:
        return (
            hasattr(instance, '__getitem__')
            and hasattr(instance, 'items')
            and callable(instance.items)
            and type(instance) != type
        )


class LaxMapping(metaclass=MetaLaxMapping):
    pass


class MetaDataClassType(type):
    def __instancecheck__(self, instance: Any) -> bool:
        from dataclasses import is_dataclass

        return is_dataclass(instance)


class DataClassType(metaclass=MetaDataClassType):
    pass


class MetaSQLAlchemyClassType(type):
    def __instancecheck__(self, instance: Any) -> bool:
        try:
            from sqlalchemy.orm import DeclarativeBase
        except ImportError:
            pass
        else:
            if isinstance(instance, DeclarativeBase):
                return True

        try:
            from sqlalchemy.ext.declarative import DeclarativeMeta
        except ImportError:
            pass
        else:
            return isinstance(instance.__class__, DeclarativeMeta)

        return False


class SQLAlchemyClassType(metaclass=MetaSQLAlchemyClassType):
    pass
