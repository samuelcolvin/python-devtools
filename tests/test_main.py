import re
import sys
from collections.abc import Generator
from pathlib import Path
from subprocess import PIPE, run

import pytest

from devtools import Debug, debug
from devtools.ansi import strip_ansi

from .utils import normalise_output


def test_print(capsys):
    a = 1
    b = 2
    result = debug(a, b)
    stdout, stderr = capsys.readouterr()
    print(stdout)
    assert normalise_output(stdout) == (
        'tests/test_main.py:<line no> test_print\n'
        '    a: 1 (int)\n'
        '    b: 2 (int)\n'
    )
    assert stderr == ''
    assert result == (1, 2)


def test_print_kwargs(capsys):
    a = 1
    b = 2
    result = debug(a, b, foo=[1, 2, 3])
    stdout, stderr = capsys.readouterr()
    print(stdout)
    assert normalise_output(stdout) == (
        'tests/test_main.py:<line no> test_print_kwargs\n'
        '    a: 1 (int)\n'
        '    b: 2 (int)\n'
        '    foo: [1, 2, 3] (list) len=3\n'
    )
    assert stderr == ''
    assert result == (1, 2, {'foo': [1, 2, 3]})


def test_print_generator(capsys):
    gen = (i for i in [1, 2])

    result = debug(gen)
    stdout, stderr = capsys.readouterr()
    print(stdout)
    assert normalise_output(stdout) == (
        'tests/test_main.py:<line no> test_print_generator\n'
        '    gen: (\n'
        '        1,\n'
        '        2,\n'
        '    ) (generator)\n'
    )
    assert stderr == ''
    assert isinstance(result, Generator)
    # the generator got evaluated and is now empty, that's correct currently
    assert list(result) == []


def test_format():
    a = b'i might bite'
    b = "hello this is a test"
    v = debug.format(a, b)
    s = normalise_output(str(v))
    print(s)
    assert s == (
        "tests/test_main.py:<line no> test_format\n"
        "    a: b'i might bite' (bytes) len=12\n"
        "    b: 'hello this is a test' (str) len=20"
    )


@pytest.mark.xfail(
    sys.platform == 'win32',
    reason='Fatal Python error: _Py_HashRandomization_Init: failed to get random numbers to initialize Python',
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
        "running debug...\n"
        "/path/to/test.py:8 <module>\n"
        "    foobar: 'hello world' (str) len=11\n"
        "/path/to/test.py:4 test_func\n"
        "    'in test func' (str) len=12\n"
        "    v: 42 (int)\n"
        "debug run.\n"
    )


def test_odd_path(mocker):
    # all valid calls
    mocked_relative_to = mocker.patch('pathlib.Path.relative_to')
    mocked_relative_to.side_effect = ValueError()
    v = debug.format('test')
    if sys.platform == "win32":
        pattern = r"\w:\\.*?\\"
    else:
        pattern = r"/.*?/"
    pattern += r"test_main.py:\d{2,} test_odd_path\n    'test' \(str\) len=4"
    assert re.search(pattern, str(v)), v


def test_small_call_frame():
    debug_ = Debug(warnings=False)
    v = debug_.format(
        1,
        2,
        3,
    )
    assert normalise_output(str(v)) == (
        'tests/test_main.py:<line no> test_small_call_frame\n'
        '    1 (int)\n'
        '    2 (int)\n'
        '    3 (int)'
    )


def test_small_call_frame_warning():
    debug_ = Debug()
    v = debug_.format(
        1,
        2,
        3,
    )
    print('\n---\n{}\n---'.format(v))
    assert normalise_output(str(v)) == (
        'tests/test_main.py:<line no> test_small_call_frame_warning\n'
        '    1 (int)\n'
        '    2 (int)\n'
        '    3 (int)'
    )


@pytest.mark.skipif(sys.version_info < (3, 6), reason='kwarg order is not guaranteed for 3.5')
def test_kwargs():
    a = 'variable'
    v = debug.format(first=a, second='literal')
    s = normalise_output(str(v))
    print(s)
    assert s == (
        "tests/test_main.py:<line no> test_kwargs\n"
        "    first: 'variable' (str) len=8 variable=a\n"
        "    second: 'literal' (str) len=7"
    )


def test_kwargs_orderless():
    # for python3.5
    a = 'variable'
    v = debug.format(first=a, second='literal')
    s = normalise_output(str(v))
    assert set(s.split('\n')) == {
        "tests/test_main.py:<line no> test_kwargs_orderless",
        "    first: 'variable' (str) len=8 variable=a",
        "    second: 'literal' (str) len=7",
    }


def test_simple_vars():
    v = debug.format('test', 1, 2)
    s = normalise_output(str(v))
    assert s == (
        "tests/test_main.py:<line no> test_simple_vars\n"
        "    'test' (str) len=4\n"
        "    1 (int)\n"
        "    2 (int)"
    )
    r = normalise_output(repr(v))
    assert r == (
        "<DebugOutput tests/test_main.py:<line no> test_simple_vars arguments: 'test' (str) len=4 1 (int) 2 (int)>"
    )


def test_attributes():
    class Foo:
        x = 1

    class Bar:
        y = Foo()

    b = Bar()
    v = debug.format(b.y.x)
    assert 'test_attributes\n    b.y.x: 1 (int)' in str(v)


def test_eval():
    v = eval('debug.format(1)')

    assert str(v) == '<string>:1 <module> (no code context for debug call, code inspection impossible)\n    1 (int)'


def test_warnings_disabled():
    debug_ = Debug(warnings=False)
    v1 = eval('debug_.format(1)')
    assert str(v1) == '<string>:1 <module>\n    1 (int)'
    v2 = debug_.format(1)
    assert 'test_warnings_disabled\n    1 (int)' in str(v2)


def test_eval_kwargs():
    v = eval('debug.format(1, apple="pear")')

    assert set(str(v).split('\n')) == {
        "<string>:1 <module> (no code context for debug call, code inspection impossible)",
        "    1 (int)",
        "    apple: 'pear' (str) len=4",
    }


def test_exec(capsys):
    exec(
        'a = 1\n'
        'b = 2\n'
        'debug(b, a + b)'
    )

    stdout, stderr = capsys.readouterr()
    assert stdout == (
        '<string>:3 <module> (no code context for debug call, code inspection impossible)\n'
        '    2 (int)\n'
        '    3 (int)\n'
    )
    assert stderr == ''


def test_colours():
    v = debug.format(range(6))
    s = v.str(True)
    assert s.startswith('\x1b[35mtests'), repr(s)
    s2 = normalise_output(strip_ansi(s))
    assert s2 == normalise_output(v.str()), repr(s2)


def test_colours_warnings(mocker):
    mocked_getframe = mocker.patch('sys._getframe')
    mocked_getframe.side_effect = ValueError()
    v = debug.format('x')
    s = normalise_output(v.str(True))
    assert s.startswith('\x1b[35m<unknown>'), repr(s)
    s2 = strip_ansi(s)
    assert s2 == v.str(), repr(s2)


def test_inspect_error(mocker):
    mocked_getframe = mocker.patch('sys._getframe')
    mocked_getframe.side_effect = ValueError()
    v = debug.format('x')
    print(repr(str(v)))
    assert str(v) == "<unknown>:0  (error parsing code, call stack too shallow)\n    'x' (str) len=1"


def test_breakpoint(mocker):
    # not much else we can do here
    mocked_set_trace = mocker.patch('pdb.Pdb.set_trace')
    debug.breakpoint()
    assert mocked_set_trace.called


@pytest.mark.xfail(
    sys.platform == 'win32' and sys.version_info >= (3, 9),
    reason='see https://github.com/alexmojaki/executing/issues/27',
)
def test_starred_kwargs():
    v = {'foo': 1, 'bar': 2}
    v = debug.format(**v)
    s = normalise_output(v.str())
    assert set(s.split('\n')) == {
        'tests/test_main.py:<line no> test_starred_kwargs',
        '    foo: 1 (int)',
        '    bar: 2 (int)',
    }


@pytest.mark.skipif(sys.version_info < (3, 7), reason='error repr different before 3.7')
def test_pretty_error():
    class BadPretty:
        def __getattr__(self, item):
            raise RuntimeError('this is an error')

    b = BadPretty()
    v = debug.format(b)
    s = normalise_output(str(v))
    assert s == (
        "tests/test_main.py:<line no> test_pretty_error\n"
        "    b: <tests.test_main.test_pretty_error.<locals>.BadPretty object at 0x<hash>> (BadPretty)\n"
        "    !!! error pretty printing value: RuntimeError('this is an error')"
    )


def test_multiple_debugs():
    debug.format([i * 2 for i in range(2)])
    debug.format([i * 2 for i in range(2)])
    v = debug.format([i * 2 for i in range(2)])
    s = normalise_output(str(v))
    assert s == (
        'tests/test_main.py:<line no> test_multiple_debugs\n'
        '    [i * 2 for i in range(2)]: [0, 2] (list) len=2'
    )


def test_return_args(capsys):
    assert debug('foo') == 'foo'
    assert debug('foo', 'bar') == ('foo', 'bar')
    assert debug('foo', 'bar', spam=123) == ('foo', 'bar', {'spam': 123})
    assert debug(spam=123) == ({'spam': 123},)
    stdout, stderr = capsys.readouterr()
    print(stdout)
