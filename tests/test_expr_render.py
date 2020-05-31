import ast
import asyncio
import re
import sys

import pytest

from devtools import Debug, debug


def foobar(a, b, c):
    return a + b + c


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_simple():
    a = [1, 2, 3]
    v = debug.format(len(a))
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_simple\n'
        '    len(a): 3 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_subscription():
    a = {1: 2}
    v = debug.format(a[1])
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_subscription\n'
        '    a[1]: 2 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_exotic_types():
    aa = [1, 2, 3]
    v = debug.format(
        sum(aa),
        1 == 2,
        1 < 2,
        1 << 2,
        't' if True else 'f',
        1 or 2,
        [a for a in aa],
        {a for a in aa},
        {a: a + 1 for a in aa},
        (a for a in aa),
    )
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    s = re.sub(r'(at 0x)\w+', r'\1<hash>', s)
    print('\n---\n{}\n---'.format(v))
    # list and generator comprehensions are wrong because ast is wrong, see https://bugs.python.org/issue31241
    assert (
        "tests/test_expr_render.py:<line no> test_exotic_types\n"
        "    sum(aa): 6 (int)\n"
        "    1 == 2: False (bool)\n"
        "    1 < 2: True (bool)\n"
        "    1 << 2: 4 (int)\n"
        "    't' if True else 'f': 't' (str) len=1\n"
        "    1 or 2: 1 (int)\n"
        "    [a for a in aa]: [1, 2, 3] (list) len=3\n"
        "    {a for a in aa}: {1, 2, 3} (set) len=3\n"
        "    {a: a + 1 for a in aa}: {\n"
        "        1: 2,\n"
        "        2: 3,\n"
        "        3: 4,\n"
        "    } (dict) len=3\n"
        "    (a for a in aa): (\n"
        "        1,\n"
        "        2,\n"
        "        3,\n"
        "    ) (generator)"
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_newline():
    v = debug.format(
        foobar(1, 2, 3))
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_newline\n'
        '    foobar(1, 2, 3): 6 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_trailing_bracket():
    v = debug.format(
        foobar(1, 2, 3)
    )
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_trailing_bracket\n'
        '    foobar(1, 2, 3): 6 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_multiline():
    v = debug.format(
        foobar(1,
               2,
               3)
    )
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_multiline\n'
        '    foobar(1, 2, 3): 6 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_multiline_trailing_bracket():
    v = debug.format(
        foobar(1, 2, 3
               ))
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_multiline_trailing_bracket\n'
        '    foobar(1, 2, 3 ): 6 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_kwargs():
    v = debug.format(
        foobar(1, 2, 3),
        a=6,
        b=7
    )
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_kwargs\n'
        '    foobar(1, 2, 3): 6 (int)\n'
        '    a: 6 (int)\n'
        '    b: 7 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_kwargs_multiline():
    v = debug.format(
        foobar(1, 2,
               3),
        a=6,
        b=7
    )
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_kwargs_multiline\n'
        '    foobar(1, 2, 3): 6 (int)\n'
        '    a: 6 (int)\n'
        '    b: 7 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_multiple_trailing_lines():
    v = debug.format(
        foobar(
            1, 2, 3
        ),
    )
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_multiple_trailing_lines\n    foobar( 1, 2, 3 ): 6 (int)'
    ) == s


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_very_nested_last_statement():
    def func():
        return debug.format(
            abs(
                abs(
                    abs(
                        abs(
                            -1
                        )
                    )
                )
            )
        )

    v = func()
    # check only the original code is included in the warning
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> func\n'
        '    abs( abs( abs( abs( -1 ) ) ) ): 1 (int)'
    )


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_syntax_warning():
    def func():
        return debug.format(
            abs(
                abs(
                    abs(
                        abs(
                            abs(
                                -1
                            )
                        )
                    )
                )
            )
        )

    v = func()
    # check only the original code is included in the warning
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> func '
        '(error parsing code, SyntaxError: unexpected EOF while parsing (test_expr_render.py, line 8))\n'
        '    1 (int)'
    )


def test_no_syntax_warning():
    # exceed the 4 extra lines which are normally checked
    debug_ = Debug(warnings=False)

    def func():
        return debug_.format(
            abs(
                abs(
                    abs(
                        abs(
                            abs(
                                -1
                            )
                        )
                    )
                )
            )
        )

    v = func()
    assert '(error parsing code' not in str(v)
    assert 'func' in str(v)


@pytest.mark.xfail(sys.platform == 'win32', reason='yet unknown windows problem')
def test_await():
    async def foo():
        return 1

    async def bar():
        return debug.format(await foo())

    loop = asyncio.get_event_loop()
    v = loop.run_until_complete(bar())
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    assert (
        'tests/test_expr_render.py:<line no> bar\n'
        '    1 (int)'
    ) == s


def test_other_debug_arg():
    debug.timer()
    v = debug.format([1, 2])

    # check only the original code is included in the warning
    s = re.sub(r':\d{2,}', ':<line no>', str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_other_debug_arg\n'
        '    [1, 2] (list) len=2'
    )


def test_wrong_ast_type(mocker):
    mocked_ast_parse = mocker.patch('ast.parse')

    code = 'async def wrapper():\n x = "foobar"'
    mocked_ast_parse.return_value = ast.parse(code, filename='testing.py').body[0].body[0].value
    v = debug.format('x')
    assert "(error parsing code, found <class 'unittest.mock.MagicMock'> not Call)" in v.str()
