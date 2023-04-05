import os
import sys

import pytest

from devtools.pytest_plugin import load_black

pytestmark = pytest.mark.skipif(sys.version_info < (3, 8), reason='requires Python 3.8+')


config = "pytest_plugins = ['devtools.pytest_plugin']"
# language=Python
default_test = """\
def test_ok():
    assert 1 + 2 == 3

def test_string_assert(insert_assert):
    thing = 'foobar'
    insert_assert(thing)\
"""


def test_insert_assert(pytester_pretty):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    test_file = pytester_pretty.makepyfile(default_test)
    result = pytester_pretty.runpytest()
    result.assert_outcomes(passed=2)
    # print(result.outlines)
    assert test_file.read_text() == (
        'def test_ok():\n'
        '    assert 1 + 2 == 3\n'
        '\n'
        'def test_string_assert(insert_assert):\n'
        "    thing = 'foobar'\n"
        '    # insert_assert(thing)\n'
        '    assert thing == "foobar"'
    )


def test_insert_assert_no_pretty(pytester):
    os.environ.pop('CI', None)
    pytester.makeconftest(config)
    test_file = pytester.makepyfile(default_test)
    result = pytester.runpytest('-p', 'no:pretty')
    result.assert_outcomes(passed=2)
    assert test_file.read_text() == (
        'def test_ok():\n'
        '    assert 1 + 2 == 3\n'
        '\n'
        'def test_string_assert(insert_assert):\n'
        "    thing = 'foobar'\n"
        '    # insert_assert(thing)\n'
        '    assert thing == "foobar"'
    )


def test_insert_assert_print(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    test_file = pytester_pretty.makepyfile(default_test)
    # assert r == 0
    result = pytester_pretty.runpytest('--insert-assert-print')
    result.assert_outcomes(passed=2)
    assert test_file.read_text() == default_test
    captured = capsys.readouterr()
    assert 'test_insert_assert_print.py - 6:' in captured.out
    assert 'Printed 1 insert_assert() call in 1 file\n' in captured.out


def test_insert_assert_fail(pytester_pretty):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    test_file = pytester_pretty.makepyfile(default_test)
    # assert r == 0
    result = pytester_pretty.runpytest()
    assert result.parseoutcomes() == {'passed': 2, 'warning': 1, 'insert': 1}
    assert test_file.read_text() != default_test


def test_deep(pytester_pretty):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    # language=Python
    test_file = pytester_pretty.makepyfile(
        """
    def test_deep(insert_assert):
        insert_assert([{'a': i, 'b': 2 * 2} for i in range(3)])
    """
    )
    result = pytester_pretty.runpytest()
    result.assert_outcomes(passed=1)
    assert test_file.read_text() == (
        'def test_deep(insert_assert):\n'
        "    # insert_assert([{'a': i, 'b': 2 * 2} for i in range(3)])\n"
        '    assert [{"a": i, "b": 2 * 2} for i in range(3)] == [\n'
        '        {"a": 0, "b": 4},\n'
        '        {"a": 1, "b": 4},\n'
        '        {"a": 2, "b": 4},\n'
        '    ]'
    )


def test_enum(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    # language=Python
    pytester_pretty.makepyfile(
        """
from enum import Enum

class Foo(Enum):
    A = 1
    B = 2

def test_deep(insert_assert):
    x = Foo.A
    insert_assert(x)
    """
    )
    result = pytester_pretty.runpytest('--insert-assert-print')
    result.assert_outcomes(passed=1)
    captured = capsys.readouterr()
    assert '    assert x == Foo.A\n' in captured.out


def test_insert_assert_black(tmp_path):
    old_wd = os.getcwd()
    try:
        os.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            """\
[tool.black]
target-version = ["py39"]
skip-string-normalization = true"""
        )
        load_black.cache_clear()
    finally:
        os.chdir(old_wd)

    f = load_black()
    # no string normalization
    assert f("'foobar'") == "'foobar'\n"


def test_insert_assert_repeat(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    test_file = pytester_pretty.makepyfile(
        """\
import pytest

@pytest.mark.parametrize('x', [1, 2, 3])
def test_string_assert(x, insert_assert):
    insert_assert(x)\
"""
    )
    result = pytester_pretty.runpytest()
    result.assert_outcomes(passed=3)
    assert test_file.read_text() == (
        'import pytest\n'
        '\n'
        "@pytest.mark.parametrize('x', [1, 2, 3])\n"
        'def test_string_assert(x, insert_assert):\n'
        '    # insert_assert(x)\n'
        '    assert x == 1'
    )
    captured = capsys.readouterr()
    assert '2 insert skipped because an assert statement on that line had already be inserted!\n' in captured.out
