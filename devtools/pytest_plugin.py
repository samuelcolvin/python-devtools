from __future__ import annotations as _annotations

import ast
import builtins
import sys
import textwrap
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from itertools import groupby
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING, Any, Callable, Generator, Sized

import pytest
from executing import Source

from . import debug

if TYPE_CHECKING:
    pass

__all__ = ('insert_assert',)


@dataclass
class ToReplace:
    file: Path
    start_line: int
    end_line: int | None
    code: str


to_replace: list[ToReplace] = []
insert_assert_calls: ContextVar[int] = ContextVar('insert_assert_calls', default=0)
insert_assert_summary: ContextVar[list[str]] = ContextVar('insert_assert_summary')


def insert_assert(value: Any) -> int:
    call_frame: FrameType = sys._getframe(1)
    if sys.version_info < (3, 8):  # pragma: no cover
        raise RuntimeError('insert_assert() requires Python 3.8+')

    format_code = load_black()
    ex = Source.for_frame(call_frame).executing(call_frame)
    if ex.node is None:  # pragma: no cover
        python_code = format_code(str(custom_repr(value)))
        raise RuntimeError(
            f'insert_assert() was unable to find the frame from which it was called, called with:\n{python_code}'
        )
    ast_arg = ex.node.args[0]  # type: ignore[attr-defined]
    if isinstance(ast_arg, ast.Name):
        arg = ast_arg.id
    else:
        arg = ' '.join(map(str.strip, ex.source.asttokens().get_text(ast_arg).splitlines()))

    python_code = format_code(f'# insert_assert({arg})\nassert {arg} == {custom_repr(value)}')

    python_code = textwrap.indent(python_code, ex.node.col_offset * ' ')
    to_replace.append(ToReplace(Path(call_frame.f_code.co_filename), ex.node.lineno, ex.node.end_lineno, python_code))
    calls = insert_assert_calls.get() + 1
    insert_assert_calls.set(calls)
    return calls


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        '--insert-assert-print',
        action='store_true',
        default=False,
        help='Print statements that would be substituted for insert_assert(), instead of writing to files',
    )
    parser.addoption(
        '--insert-assert-fail',
        action='store_true',
        default=False,
        help='Fail tests which include one or more insert_assert() calls',
    )


@pytest.fixture(scope='session', autouse=True)
def insert_assert_add_to_builtins() -> None:
    try:
        setattr(builtins, 'insert_assert', insert_assert)
        # we also install debug here since the default script doesn't install it
        setattr(builtins, 'debug', debug)
    except TypeError:
        # happens on pypy
        pass


@pytest.fixture(autouse=True)
def insert_assert_maybe_fail(pytestconfig: pytest.Config) -> Generator[None, None, None]:
    insert_assert_calls.set(0)
    yield
    print_instead = pytestconfig.getoption('insert_assert_print')
    if not print_instead:
        count = insert_assert_calls.get()
        if count:
            pytest.fail(f'devtools-insert-assert: {count} assert{plural(count)} will be inserted', pytrace=False)


@pytest.fixture(name='insert_assert')
def insert_assert_fixture() -> Callable[[Any], int]:
    return insert_assert


def pytest_report_teststatus(report: pytest.TestReport, config: pytest.Config) -> Any:
    if report.when == 'teardown' and report.failed and 'devtools-insert-assert:' in repr(report.longrepr):
        return 'insert assert', 'i', ('INSERT ASSERT', {'cyan': True})


@pytest.fixture(scope='session', autouse=True)
def insert_assert_session(pytestconfig: pytest.Config) -> Generator[None, None, None]:
    """
    Actual logic for updating code examples.
    """
    try:
        __builtins__['insert_assert'] = insert_assert
    except TypeError:
        # happens on pypy
        pass

    yield

    if not to_replace:
        return None

    print_instead = pytestconfig.getoption('insert_assert_print')

    highlight = None
    if print_instead:
        highlight = get_pygments()

    files = 0
    dup_count = 0
    summary = []
    for file, group in groupby(to_replace, key=lambda tr: tr.file):
        # we have to substitute lines in reverse order to avoid messing up line numbers
        lines = file.read_text().splitlines()
        duplicates: set[int] = set()
        for tr in sorted(group, key=lambda x: x.start_line, reverse=True):
            if print_instead:
                hr = '-' * 80
                code = highlight(tr.code) if highlight else tr.code
                line_no = f'{tr.start_line}' if tr.start_line == tr.end_line else f'{tr.start_line}-{tr.end_line}'
                summary.append(f'{file} - {line_no}:\n{hr}\n{code}{hr}\n')
            else:
                if tr.start_line in duplicates:
                    dup_count += 1
                else:
                    duplicates.add(tr.start_line)
                    lines[tr.start_line - 1 : tr.end_line] = tr.code.splitlines()
        if not print_instead:
            file.write_text('\n'.join(lines))
        files += 1
    prefix = 'Printed' if print_instead else 'Replaced'
    summary.append(
        f'{prefix} {len(to_replace)} insert_assert() call{plural(to_replace)} in {files} file{plural(files)}'
    )
    if dup_count:
        summary.append(
            f'\n{dup_count} insert skipped because an assert statement on that line had already be inserted!'
        )

    insert_assert_summary.set(summary)
    to_replace.clear()


def pytest_terminal_summary() -> None:
    summary = insert_assert_summary.get(None)
    if summary:
        print('\n'.join(summary))


def custom_repr(value: Any) -> Any:
    if isinstance(value, (list, tuple, set, frozenset)):
        return value.__class__(map(custom_repr, value))
    elif isinstance(value, dict):
        return value.__class__((custom_repr(k), custom_repr(v)) for k, v in value.items())
    if isinstance(value, Enum):
        return PlainRepr(f'{value.__class__.__name__}.{value.name}')
    else:
        return PlainRepr(repr(value))


class PlainRepr(str):
    """
    String class where repr doesn't include quotes.
    """

    def __repr__(self) -> str:
        return str(self)


def plural(v: int | Sized) -> str:
    if isinstance(v, (int, float)):
        n = v
    else:
        n = len(v)
    return '' if n == 1 else 's'


@lru_cache(maxsize=None)
def load_black() -> Callable[[str], str]:
    """
    Build black configuration from "pyproject.toml".

    Black doesn't have a nice self-contained API for reading pyproject.toml, hence all this.
    """
    try:
        from black import format_file_contents
        from black.files import find_pyproject_toml, parse_pyproject_toml
        from black.mode import Mode, TargetVersion
        from black.parsing import InvalidInput
    except ImportError:
        return lambda x: x

    def convert_target_version(target_version_config: Any) -> set[Any] | None:
        if target_version_config is not None:
            return None
        elif not isinstance(target_version_config, list):
            raise ValueError('Config key "target_version" must be a list')
        else:
            return {TargetVersion[tv.upper()] for tv in target_version_config}

    @dataclass
    class ConfigArg:
        config_name: str
        keyword_name: str
        converter: Callable[[Any], Any]

    config_mapping: list[ConfigArg] = [
        ConfigArg('target_version', 'target_versions', convert_target_version),
        ConfigArg('line_length', 'line_length', int),
        ConfigArg('skip_string_normalization', 'string_normalization', lambda x: not x),
        ConfigArg('skip_magic_trailing_commas', 'magic_trailing_comma', lambda x: not x),
    ]

    config_str = find_pyproject_toml((str(Path.cwd()),))
    mode_ = None
    fast = False
    if config_str:
        try:
            config = parse_pyproject_toml(config_str)
        except (OSError, ValueError) as e:
            raise ValueError(f'Error reading configuration file: {e}')

        if config:
            kwargs = dict()
            for config_arg in config_mapping:
                try:
                    value = config[config_arg.config_name]
                except KeyError:
                    pass
                else:
                    value = config_arg.converter(value)
                    if value is not None:
                        kwargs[config_arg.keyword_name] = value

            mode_ = Mode(**kwargs)
            fast = bool(config.get('fast'))

    mode = mode_ or Mode()

    def format_code(code: str) -> str:
        try:
            return format_file_contents(code, fast=fast, mode=mode)
        except InvalidInput as e:
            print('black error, you will need to format the code manually,', e)
            return code

    return format_code


# isatty() is false inside pytest, hence calling this now
try:
    std_out_istty = sys.stdout.isatty()
except Exception:
    std_out_istty = False


@lru_cache(maxsize=None)
def get_pygments() -> Callable[[str], str] | None:  # pragma: no cover
    if not std_out_istty:
        return None
    try:
        import pygments
        from pygments.formatters import Terminal256Formatter
        from pygments.lexers import PythonLexer
    except ImportError as e:  # pragma: no cover
        print(e)
        return None
    else:
        pyg_lexer, terminal_formatter = PythonLexer(), Terminal256Formatter()

        def highlight(code: str) -> str:
            return pygments.highlight(code, lexer=pyg_lexer, formatter=terminal_formatter)

        return highlight
