import io
import re
import sys
from time import sleep

import pytest

from devtools import Timer, debug


@pytest.mark.skipif(sys.platform != 'linux', reason='not on linux')
def test_simple():
    f = io.StringIO()
    t = debug.timer(name='foobar', file=f)
    with t:
        sleep(0.01)
    v = f.getvalue()
    assert re.fullmatch(r'foobar: 0\.01[012]s elapsed\n', v)


@pytest.mark.skipif(sys.platform != 'linux', reason='not on linux')
def test_multiple():
    f = io.StringIO()
    t = Timer(file=f)
    for i in [0.001, 0.002, 0.003]:
        with t(i):
            sleep(i)
    t.summary()
    v = f.getvalue()
    assert re.sub(r'0\.00\d', '0.00X', v) == (
        '0.00X: 0.00Xs elapsed\n'
        '0.00X: 0.00Xs elapsed\n'
        '0.00X: 0.00Xs elapsed\n'
        '3 times: mean=0.00Xs stdev=0.00Xs min=0.00Xs max=0.00Xs\n'
    )


def test_unfinished():
    t = Timer().start()
    assert str(t.results[0]) == '-1.000s elapsed'


@pytest.mark.skipif(sys.platform != 'linux', reason='not on linux')
def test_multiple_not_verbose():
    f = io.StringIO()
    t = Timer(file=f)
    for i in [0.01, 0.02, 0.03]:
        with t(verbose=False):
            sleep(i)
    t.summary(True)
    v = re.sub('[123]s', '0s', f.getvalue())
    assert v == (
        '    0.010s elapsed\n'
        '    0.020s elapsed\n'
        '    0.030s elapsed\n'
        '3 times: mean=0.020s stdev=0.010s min=0.010s max=0.030s\n'
    )


def test_unfinished_summary():
    f = io.StringIO()
    t = Timer(file=f).start()
    t.summary()
    v = f.getvalue()
    assert v == '1 times: mean=0.000s stdev=0.000s min=0.000s max=0.000s\n'


def test_summary_not_started():
    with pytest.raises(RuntimeError):
        Timer().summary()
