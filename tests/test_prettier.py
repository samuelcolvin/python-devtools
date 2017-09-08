import string

import numpy

from devtools.prettier import PrettyFormat, pformat, pprint


def test_dict():
    v = pformat({1: 2, 3: 4})
    print(v)
    assert v == (
        '{\n'
        '    1: 2,\n'
        '    3: 4,\n'
        '}')


def test_print(capsys):
    pprint({1: 2, 3: 4})
    stdout, stderr = capsys.readouterr()
    assert stdout.startswith('\x1b')
    assert stderr == ''


def test_list():
    v = pformat(list(range(6)))
    assert v == (
        '[\n'
        '    0,\n'
        '    1,\n'
        '    2,\n'
        '    3,\n'
        '    4,\n'
        '    5,\n'
        ']')


def test_set():
    v = pformat(set(range(5)))
    assert v == (
        '{\n'
        '    0,\n'
        '    1,\n'
        '    2,\n'
        '    3,\n'
        '    4,\n'
        '}')


def test_tuple():
    v = pformat(tuple(range(5)))
    assert v == (
        '(\n'
        '    0,\n'
        '    1,\n'
        '    2,\n'
        '    3,\n'
        '    4,\n'
        ')')


def test_generator():
    v = pformat((i for i in range(3)))
    assert v == (
        '(\n'
        '    0,\n'
        '    1,\n'
        '    2,\n'
        ')')


def test_generator_no_yield():
    pformat_ = PrettyFormat(yield_from_generators=False)
    v = pformat_((i for i in range(3)))
    assert v.startswith('<generator object test_generator_no_yield.<locals>.<genexpr> at ')


def test_str():
    pformat_ = PrettyFormat(max_width=12)
    v = pformat_(string.ascii_lowercase + '\n' + string.digits)
    assert v == (
        "(\n"
        "    'abcdefghijklmnopqrstuvwxyz\\n'\n"
        "    '0123456789'\n"
        ")")


def test_str_repr():
    pformat_ = PrettyFormat(repr_strings=True)
    v = pformat_(string.ascii_lowercase + '\n' + string.digits)
    assert v == "'abcdefghijklmnopqrstuvwxyz\\n0123456789'"


def test_bytes():
    pformat_ = PrettyFormat(max_width=12)
    v = pformat_(string.ascii_lowercase.encode())
    assert v == """(
    b'abcde'
    b'fghij'
    b'klmno'
    b'pqrst'
    b'uvwxy'
    b'z'
)"""


def test_short_bytes():
    assert "b'abcdefghijklmnopqrstuvwxyz'" == pformat(string.ascii_lowercase.encode())


def test_indent_numpy():
    v = pformat({'numpy test': numpy.array(range(20))})
    assert v == """{
    'numpy test': (
        array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16,
               17, 18, 19])
    ),
}"""


def test_indent_numpy_short():
    v = pformat({'numpy test': numpy.array(range(10))})
    assert v == """{
    'numpy test': array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
}"""
