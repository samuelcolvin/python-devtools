import asyncio
import sys

import pytest

from devtools import Debug, debug

from .utils import normalise_output


def foobar(a, b, c):
    return a + b + c


def test_simple():
    a = [1, 2, 3]
    v = debug.format(len(a))
    s = normalise_output(str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_simple\n'
        '    len(a): 3 (int)'
    ) == s


def test_subscription():
    a = {1: 2}
    v = debug.format(a[1])
    s = normalise_output(str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_subscription\n'
        '    a[1]: 2 (int)'
    ) == s


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
    s = normalise_output(str(v))
    print('\n---\n{}\n---'.format(v))

    # Generator expression source changed in 3.8 to include parentheses, see:
    # https://github.com/gristlabs/asttokens/pull/50
    # https://bugs.python.org/issue31241
    genexpr_source = "a for a in aa"
    if sys.version_info[:2] > (3, 7):
        genexpr_source = f"({genexpr_source})"

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
        f"    {genexpr_source}: (\n"
        "        1,\n"
        "        2,\n"
        "        3,\n"
        "    ) (generator)"
    ) == s


def test_newline():
    v = debug.format(
        foobar(1, 2, 3))
    s = normalise_output(str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_newline\n'
        '    foobar(1, 2, 3): 6 (int)'
    ) == s


def test_trailing_bracket():
    v = debug.format(
        foobar(1, 2, 3)
    )
    s = normalise_output(str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_trailing_bracket\n'
        '    foobar(1, 2, 3): 6 (int)'
    ) == s


def test_multiline():
    v = debug.format(
        foobar(1,
               2,
               3)
    )
    s = normalise_output(str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_multiline\n'
        '    foobar(1, 2, 3): 6 (int)'
    ) == s


def test_multiline_trailing_bracket():
    v = debug.format(
        foobar(1, 2, 3
               ))
    s = normalise_output(str(v))
    # print(s)
    assert (
        'tests/test_expr_render.py:<line no> test_multiline_trailing_bracket\n'
        '    foobar(1, 2, 3 ): 6 (int)'
    ) == s


@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_kwargs():
    v = debug.format(
        foobar(1, 2, 3),
        a=6,
        b=7
    )
    s = normalise_output(str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_kwargs\n'
        '    foobar(1, 2, 3): 6 (int)\n'
        '    a: 6 (int)\n'
        '    b: 7 (int)'
    ) == s


@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_kwargs_multiline():
    v = debug.format(
        foobar(1, 2,
               3),
        a=6,
        b=7
    )
    s = normalise_output(str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_kwargs_multiline\n'
        '    foobar(1, 2, 3): 6 (int)\n'
        '    a: 6 (int)\n'
        '    b: 7 (int)'
    ) == s


def test_multiple_trailing_lines():
    v = debug.format(
        foobar(
            1, 2, 3
        ),
    )
    s = normalise_output(str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_multiple_trailing_lines\n    foobar( 1, 2, 3 ): 6 (int)'
    ) == s


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
    s = normalise_output(str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_very_nested_last_statement.<locals>.func\n'
        '    abs( abs( abs( abs( -1 ) ) ) ): 1 (int)'
    )


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
    s = normalise_output(str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_syntax_warning.<locals>.func\n'
        '    abs( abs( abs( abs( abs( -1 ) ) ) ) ): 1 (int)'
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
    s = normalise_output(str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_no_syntax_warning.<locals>.func\n'
        '    abs( abs( abs( abs( abs( -1 ) ) ) ) ): 1 (int)'
    )


def test_await():
    async def foo():
        return 1

    async def bar():
        return debug.format(await foo())

    loop = asyncio.new_event_loop()
    v = loop.run_until_complete(bar())
    loop.close()
    s = normalise_output(str(v))
    assert (
        'tests/test_expr_render.py:<line no> test_await.<locals>.bar\n'
        '    await foo(): 1 (int)'
    ) == s


def test_other_debug_arg():
    debug.timer()
    v = debug.format([1, 2])

    # check only the original code is included in the warning
    s = normalise_output(str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_other_debug_arg\n'
        '    [1, 2] (list) len=2'
    )


def test_other_debug_arg_not_literal():
    debug.timer()
    x = 1
    y = 2
    v = debug.format([x, y])

    s = normalise_output(str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_other_debug_arg_not_literal\n'
        '    [x, y]: [1, 2] (list) len=2'
    )


def test_executing_failure():
    debug.timer()
    x = 1
    y = 2

    # executing fails inside a pytest assert ast the AST is modified
    assert normalise_output(str(debug.format([x, y]))) == (
        'tests/test_expr_render.py:<line no> test_executing_failure '
        '(executing failed to find the calling node)\n'
        '    [1, 2] (list) len=2'
    )


def test_format_inside_error():
    debug.timer()
    x = 1
    y = 2
    try:
        raise RuntimeError(debug.format([x, y]))
    except RuntimeError as e:
        v = str(e)

    s = normalise_output(str(v))
    assert s == (
        'tests/test_expr_render.py:<line no> test_format_inside_error\n'
        '    [x, y]: [1, 2] (list) len=2'
    )
