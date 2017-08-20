import re
import sys

import pytest

from devtools import debug


def foobar(a, b, c):
    return a + b + c


def test_simple():
    a = [1, 2, 3]
    v = debug.format(len(a))
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert s == (
        'tests/test_expr_render.py:<line no> test_simple: len(a) = 3 (int)'
    )


def test_newline():
    v = debug.format(
        foobar(1, 2, 3))
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert s == (
        'tests/test_expr_render.py:<line no> test_newline: foobar(1, 2, 3) = 6 (int)'
    )


def test_trailing_bracket():
    v = debug.format(
        foobar(1, 2, 3)
    )
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert s == (
        'tests/test_expr_render.py:<line no> test_trailing_bracket: foobar(1, 2, 3) = 6 (int)'
    )


def test_multiline():
    v = debug.format(
        foobar(1,
               2,
               3)
    )
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert s == (
        'tests/test_expr_render.py:<line no> test_multiline: foobar(1, 2, 3) = 6 (int)'
    )


def test_multiline_trailing_bracket():
    v = debug.format(
        foobar(1, 2, 3
               ))
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert s == (
        'tests/test_expr_render.py:<line no> test_multiline_trailing_bracket: foobar(1, 2, 3 ) = 6 (int)'
    )


@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_kwargs():
    v = debug.format(
        foobar(1, 2, 3),
        a=6,
        b=7
    )
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_kwargs\n'
        '  foobar(1, 2, 3) = 6 (int)\n'
        '  a = 6 (int)\n'
        '  b = 7 (int)'

    )


@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_kwargs_multiline():
    v = debug.format(
        foobar(1, 2,
               3),
        a=6,
        b=7
    )
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_kwargs_multiline\n'
        '  foobar(1, 2, 3) = 6 (int)\n'
        '  a = 6 (int)\n'
        '  b = 7 (int)'

    )
