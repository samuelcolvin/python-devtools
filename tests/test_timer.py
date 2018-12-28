import io
import re
from time import sleep

import pytest

from devtools import Timer, debug


def test_simple():
    f = io.StringIO()
    t = debug.timer(name='foobar', file=f)
    with t:
        sleep(0.01)
    v = f.getvalue()
    assert re.fullmatch(r'foobar: 0\.01[012]s elapsed\n', v)


def test_multiple():
    f = io.StringIO()
    t = Timer(file=f)
    for i in [0.001, 0.002, 0.003]:
        with t(i):
            sleep(i)
    t.summary()
    v = f.getvalue()
    assert v == (
        '0.001: 0.001s elapsed\n'
        '0.002: 0.002s elapsed\n'
        '0.003: 0.003s elapsed\n'
        '3 times: mean=0.002s stdev=0.001s min=0.001s max=0.003s\n'
    )


def test_unfinished():
    t = Timer().start()
    assert str(t.results[0]) == '-1.000s elapsed'


def test_multiple_not_verbose():
    f = io.StringIO()
    t = Timer(file=f)
    for i in [0.001, 0.002, 0.003]:
        with t(verbose=False):
            sleep(i)
    t.summary(True)
    v = f.getvalue()
    assert v == (
        '    0.001s elapsed\n'
        '    0.002s elapsed\n'
        '    0.003s elapsed\n'
        '3 times: mean=0.002s stdev=0.001s min=0.001s max=0.003s\n'
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
