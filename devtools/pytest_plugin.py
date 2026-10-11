from __future__ import annotations as _annotations

import ast
import builtins
import sys
import textwrap
from collections.abc import Callable, Generator, Sized
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from functools import cache
from itertools import groupby
from pathlib import Path
from types import FrameType
from typing import Any, cast

import pytest
from executing import Source

from . import debug

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
    call_frame: FrameType = sys._getframe(1)  # pyright: ignore[reportPrivateUsage]
    format_code = load_black()
    ex = Source.for_frame(call_frame).executing(call_frame)
    # executing annotates `node` as never being `None`, but it is when the calling node can't be found
    if ex.node is None:  # pragma: no cover  # pyright: ignore[reportUnnecessaryComparison]
        python_code = format_code(str(custom_repr(value)))
        raise RuntimeError(
            f'insert_assert() was unable to find the frame from which it was called, called with:\n{python_code}'
        )
    call_node = cast(ast.Call, ex.node)
    ast_arg = call_node.args[0]
    if isinstance(ast_arg, ast.Name):
        arg = ast_arg.id
    else:
        arg = ' '.join(map(str.strip, ex.source.asttokens().get_text(ast_arg).splitlines()))  # pyright: ignore[reportUnknownMemberType]

    python_code = format_code(f'# insert_assert({arg})\nassert {arg} == {custom_repr(value)}')

    python_code = textwrap.indent(python_code, call_node.col_offset * ' ')
    to_replace.append(
        ToReplace(Path(call_frame.f_code.co_filename), call_node.lineno, call_node.end_lineno, python_code)
    )
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
        setattr(builtins, 'insert_assert', insert_assert)  # noqa: B010
        # we also install debug here since the default script doesn't install it
        setattr(builtins, 'debug', debug)  # noqa: B010
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
    summary: list[str] = []
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
        seq = cast('list[Any] | tuple[Any, ...] | set[Any] | frozenset[Any]', value)
        return seq.__class__(map(custom_repr, seq))
    elif isinstance(value, dict):
        mapping = cast('dict[Any, Any]', value)
        return mapping.__class__((custom_repr(k), custom_repr(v)) for k, v in mapping.items())
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


@cache
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

    def convert_target_version(target_version_config: object) -> set[TargetVersion] | None:
        if target_version_config is None:
            return None
        elif not isinstance(target_version_config, list):
            raise ValueError('Config key "target_version" must be a list')
        else:
            versions = cast('list[str]', target_version_config)
            return {TargetVersion[tv.upper()] for tv in versions}

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
    mode_: Mode | None = None
    fast = False
    if config_str:
        try:
            config = parse_pyproject_toml(config_str)
        except (OSError, ValueError) as e:
            raise ValueError(f'Error reading configuration file: {e}')

        if config:
            kwargs: dict[str, Any] = {}
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


@cache
def get_pygments() -> Callable[[str], str] | None:  # pragma: no cover
    if not std_out_istty:
        return None
    try:
        import pygments
        from pygments.formatters import Terminal256Formatter
        from pygments.lexer import Lexer
        from pygments.lexers import PythonLexer  # pyright: ignore[reportUnknownVariableType]
    except ImportError as e:  # pragma: no cover
        print(e)
        return None
    else:
        pyg_lexer = cast('Lexer', PythonLexer())
        terminal_formatter: Terminal256Formatter[str] = Terminal256Formatter()

        def highlight(code: str) -> str:
            return pygments.highlight(code, lexer=pyg_lexer, formatter=terminal_formatter)

        return highlight
