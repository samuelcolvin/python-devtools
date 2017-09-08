import re
import sys
from pathlib import Path
from subprocess import PIPE, run

import pytest

from devtools import Debug, debug


def test_print(capsys):
    a = 1
    b = 2
    debug(a, b)
    stdout, stderr = capsys.readouterr()
    print(stdout)
    assert re.sub(':\d{2,}', ':<line no>', stdout) == (
        'tests/test_main.py:<line no> test_print\n'
        '  a = 1 (int)\n'
        '  b = 2 (int)\n'
    )
    assert stderr == ''


def test_format():
    a = b'i might bite'
    b = "hello this is a test"
    v = debug.format(a, b)
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    print(repr(s))
    assert s == (
        'tests/test_main.py:<line no> test_format\n'
        '  a = b\'i might bite\' (bytes) len=12\n'
        '  b = "hello this is a test" (str) len=20'
    )


def test_print_subprocess(tmpdir):
    f = tmpdir.join('test.py')
    f.write("""\
from devtools import debug

def test_func(v):
    debug('in test func', v)

foobar = 'hello world'
print('running debug...')
debug(foobar)
test_func(42)
print('debug run.')
    """)
    env = {'PYTHONPATH': str(Path(__file__).parent.parent.resolve())}
    p = run([sys.executable, str(f)], stdout=PIPE, stderr=PIPE, universal_newlines=True, env=env)
    assert p.stderr == ''
    assert p.returncode == 0, (p.stderr, p.stdout)
    assert p.stdout.replace(str(f), '/path/to/test.py') == (
        'running debug...\n'
        '/path/to/test.py:8 <module>: foobar = "hello world" (str) len=11\n'
        '/path/to/test.py:4 test_func\n'
        '  "in test func" (str) len=12\n'
        '  v = 42 (int)\n'
        'debug run.\n'
    )


def test_odd_path(mocker):
    # all valid calls
    mocked_relative_to = mocker.patch('pathlib.Path.relative_to')
    mocked_relative_to.side_effect = ValueError()
    v = debug.format('test')
    assert re.search('/.*?/test_main.py:\d{2,} test_odd_path: "test" \(str\) len=4', str(v)), v


def test_small_call_frame():
    debug_ = Debug(warnings=False, frame_context_length=2)
    v = debug_.format(
        1,
        2,
        3,
    )
    assert re.sub(':\d{2,}', ':<line no>', str(v)) == (
        'tests/test_main.py:<line no> test_small_call_frame\n'
        '  1 (int)\n'
        '  2 (int)\n'
        '  3 (int)'
    )


def test_small_call_frame_warning():
    debug_ = Debug(frame_context_length=2)
    with pytest.warns(SyntaxWarning):
        v = debug_.format(
            1,
            2,
            3,
        )
    assert re.sub(':\d{2,}', ':<line no>', str(v)) == (
        'tests/test_main.py:<line no> test_small_call_frame_warning\n'
        '  1 (int)\n'
        '  2 (int)\n'
        '  3 (int)'
    )


@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_kwargs():
    a = 'variable'
    v = debug.format(first=a, second='literal')
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    print(s)
    assert s == (
        'tests/test_main.py:<line no> test_kwargs\n'
        '  first = "variable" (str) len=8 variable=a\n'
        '  second = "literal" (str) len=7'
    )


def test_kwargs_orderless():
    # for python3.5
    a = 'variable'
    v = debug.format(first=a, second='literal')
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    assert set(s.split('\n')) == {
        'tests/test_main.py:<line no> test_kwargs_orderless',
        '  first = "variable" (str) len=8 variable=a',
        '  second = "literal" (str) len=7',
    }


def test_simple_vars():
    v = debug.format('test', 1, 2)
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    assert s == (
        'tests/test_main.py:<line no> test_simple_vars\n'
        '  "test" (str) len=4\n'
        '  1 (int)\n'
        '  2 (int)'
    )
    r = re.sub(':\d{2,}', ':<line no>', repr(v))
    assert r == (
        '<DebugOutput tests/test_main.py:<line no> test_simple_vars arguments: "test" (str) len=4 1 (int) 2 (int)>'
    )


def test_attributes():
    class Foo:
        x = 1

    class Bar:
        y = Foo()

    b = Bar()
    v = debug.format(b.y.x)
    assert 'test_attributes: b.y.x = 1 (int)' in str(v)


def test_eval():
    with pytest.warns(RuntimeWarning):
        v = eval('debug.format(1)')

    assert str(v) == '<string>:1 <module>: 1 (int)'


def test_warnings_disabled():
    debug_ = Debug(warnings=False)
    with pytest.warns(None) as warnings:
        v1 = eval('debug_.format(1)')
        assert str(v1) == '<string>:1 <module>: 1 (int)'
        v2 = debug_.format(1)
        assert 'test_warnings_disabled: 1 (int)' in str(v2)
    assert len(warnings) == 0


@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_eval_kwargs():
    with pytest.warns(RuntimeWarning):
        v = eval('debug.format(1, apple="pear")')

    assert str(v) == (
        '<string>:1 <module>\n'
        '  1 (int)\n'
        '  apple = "pear" (str) len=4'
    )


def test_exec(capsys):
    with pytest.warns(RuntimeWarning):
        exec(
            'a = 1\n'
            'b = 2\n'
            'debug(b, a + b)'
        )

    stdout, stderr = capsys.readouterr()
    assert stdout == (
        '<string>:3 <module>\n'
        '  2 (int)\n'
        '  3 (int)\n'
    )
    assert stderr == ''
