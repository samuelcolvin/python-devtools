import os
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.version_info < (3, 8), reason='requires Python 3.8+')


config = "pytest_plugins = ['devtools.pytest_plugin']"
# language=Python
default_test = """\
import re, pytest
def test_ok():
    assert 1 + 2 == 3

def test_value_error(insert_pytest_raises):
    with insert_pytest_raises():
        raise ValueError("Such error")\
"""


def test_insert_pytest_raises(pytester_pretty):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    test_file = pytester_pretty.makepyfile(default_test)
    result = pytester_pretty.runpytest()
    result.assert_outcomes(passed=2)
    assert test_file.read_text() == (
        'import re, pytest\n'
        'def test_ok():\n'
        '    assert 1 + 2 == 3\n'
        '\n'
        'def test_value_error(insert_pytest_raises):\n'
        '    # with insert_pytest_raises():\n'
        "    with pytest.raises(ValueError, match=re.escape('Such error')):\n"
        '        raise ValueError("Such error")'
    )


def test_insert_pytest_raises_no_pretty(pytester):
    os.environ.pop('CI', None)
    pytester.makeconftest(config)
    test_file = pytester.makepyfile(default_test)
    result = pytester.runpytest('-p', 'no:pretty')
    result.assert_outcomes(passed=2)
    assert test_file.read_text() == (
        'import re, pytest\n'
        'def test_ok():\n'
        '    assert 1 + 2 == 3\n'
        '\n'
        'def test_value_error(insert_pytest_raises):\n'
        '    # with insert_pytest_raises():\n'
        "    with pytest.raises(ValueError, match=re.escape('Such error')):\n"
        '        raise ValueError("Such error")'
    )


def test_insert_pytest_raises_print(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    test_file = pytester_pretty.makepyfile(default_test)
    # assert r == 0
    result = pytester_pretty.runpytest('--insert-assert-print')
    result.assert_outcomes(passed=2)
    assert test_file.read_text() == default_test
    captured = capsys.readouterr()
    assert 'test_insert_pytest_raises_print.py - 6:' in captured.out
    assert 'Printed 1 insert_pytest_raises() call in 1 file\n' in captured.out


def test_insert_pytest_raises_fail(pytester_pretty):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    test_file = pytester_pretty.makepyfile(default_test)
    # assert r == 0
    result = pytester_pretty.runpytest()
    assert result.parseoutcomes() == {'passed': 2, 'warning': 1, 'insert': 1}
    assert test_file.read_text() != default_test


def test_insert_pytest_raises_repeat(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    test_file = pytester_pretty.makepyfile(
        """\
import pytest, re

@pytest.mark.parametrize('x', [1, 2, 3])
def test_raise_keyerror(x, insert_pytest_raises):
    with insert_pytest_raises():
        raise KeyError(x)\
"""
    )
    result = pytester_pretty.runpytest()
    result.assert_outcomes(passed=3)
    assert test_file.read_text() == (
        'import pytest, re\n'
        '\n'
        "@pytest.mark.parametrize('x', [1, 2, 3])\n"
        'def test_raise_keyerror(x, insert_pytest_raises):\n'
        '    # with insert_pytest_raises():\n'
        "    with pytest.raises(KeyError, match=re.escape('1')):\n"
        '        raise KeyError(x)'
    )
    captured = capsys.readouterr()
    assert '2 inserts skipped because an assert statement on that line had already be inserted!\n' in captured.out


def test_insert_pytest_raises_frame_not_found(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    pytester_pretty.makepyfile(
        """\
def test_raise_keyerror(insert_pytest_raises):
    eval('insert_pytest_raises().__enter__()')
"""
    )
    result = pytester_pretty.runpytest()
    result.assert_outcomes(failed=1)
    captured = capsys.readouterr()
    assert (
        'RuntimeError: insert_pytest_raises() was unable to find the frame from which it was called\n' in captured.out
    )


def test_insert_pytest_raises_called_outside_with(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    pytester_pretty.makepyfile(
        """\
def test_raise_keyerror(insert_pytest_raises):
    assert insert_pytest_raises().__enter__() == 1
"""
    )
    result = pytester_pretty.runpytest()
    result.assert_outcomes(failed=1)
    captured = capsys.readouterr()
    assert "RuntimeError: insert_pytest_raises() was called outside of a 'with' statement\n" in captured.out


def test_insert_pytest_raises_called_with_other_with_statements(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    pytester_pretty.makepyfile(
        """\
import contextlib

def test_raise_keyerror(insert_pytest_raises):
    with contextlib.nullcontext(), insert_pytest_raises():
        raise KeyError(1)
"""
    )
    result = pytester_pretty.runpytest()
    result.assert_outcomes(failed=1)
    captured = capsys.readouterr()
    assert (
        'RuntimeError: insert_pytest_raises() was called alongside other statements, this is not supported\n'
        in captured.out
    )


def test_insert_pytest_raises_called_with_no_exception(pytester_pretty, capsys):
    os.environ.pop('CI', None)
    pytester_pretty.makeconftest(config)
    pytester_pretty.makepyfile(
        """\
def test_raise_keyerror(insert_pytest_raises):
    with insert_pytest_raises():
        assert True
"""
    )
    result = pytester_pretty.runpytest()
    result.assert_outcomes(failed=1)
    captured = capsys.readouterr()
    assert 'RuntimeError: insert_pytest_raises() was called but no exception was raised\n' in captured.out
