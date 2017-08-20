import re
import sys
from pathlib import Path
from subprocess import PIPE, run

from devtools import debug


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


def test_kwargs():
    a = 'variable'
    v = debug.format(first=a, second='literal')
    s = re.sub(':\d{2,}', ':<line no>', str(v))
    # print(s)
    assert s == (
        'tests/test_main.py:<line no> test_kwargs\n'
        '  first = "variable" (str) len=8 variable=a\n'
        '  second = "literal" (str) len=7'
    )
