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


def test_print_subprocess(tmpdir):
    f = tmpdir.join('test.py')
    f.write("""\
from devtools import debug

foobar = 'hello world'
print('running debug...')
debug(foobar)
print('debug run.')
    """)
    env = {'PYTHONPATH': str(Path(__file__).parent.parent.resolve())}
    p = run([sys.executable, str(f)], stdout=PIPE, stderr=PIPE, encoding='utf8', env=env)
    assert p.stderr == ''
    assert p.returncode == 0, (p.stderr, p.stdout)
    assert p.stdout.replace(str(f), '/path/to/test.py') == (
        'running debug...\n'
        '/path/to/test.py:4 <module>: foobar = "hello world" (str)\n'
        'debug run.\n'
    )
