import string

import numpy

from devtools.prettier import PrettyFormat, pformat


def test_dict():
    v = pformat({1: 2, 3: 4})
    print(v)
    assert v == (
        '{\n'
        '    1: 2,\n'
        '    3: 4,\n'
        '}')


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
    v = pformat(set(range(6)))
    assert v == (
        '{\n'
        '    0,\n'
        '    1,\n'
        '    2,\n'
        '    3,\n'
        '    4,\n'
        '    5,\n'
        '}')


def test_generator():
    v = pformat((i for i in range(3)))
    assert v == (
        '(\n'
        '    0,\n'
        '    1,\n'
        '    2,\n'
        ')')


def test_str():
    pformat_ = PrettyFormat(max_width=12)
    v = pformat_(string.ascii_lowercase + '\n' + string.digits)
    assert v == (
        "(\n"
        "    'abcdefghijklmnopqrstuvwxyz\\n'\n"
        "    '0123456789'\n"
        ")")


def test_bytes():
    pformat_ = PrettyFormat(max_width=12)
    v = pformat_(string.ascii_lowercase.encode())
    assert v == (
        "(\n"
        "    b'abcde'\n"
        "    b'fghij'\n"
        "    b'klmno'\n"
        "    b'pqrst'\n"
        "    b'uvwxy'\n"
        "    b'z'\n"
        ")")


def test_indent_numpy():
    v = pformat({'numpy test': numpy.array(range(20))})
    assert v == ("{\n"
                 "    'numpy test': (\n"
                 "        array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16,\n"
                 "               17, 18, 19])\n"
                 "    ),\n"
                 "}")
