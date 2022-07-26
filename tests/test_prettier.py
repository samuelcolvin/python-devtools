import os
import string
from collections import Counter, OrderedDict, namedtuple
from dataclasses import dataclass
from typing import List
from unittest.mock import MagicMock

import pytest

from devtools.ansi import strip_ansi
from devtools.prettier import PrettyFormat, pformat, pprint

try:
    import numpy
except ImportError:
    numpy = None

try:
    from multidict import CIMultiDict, MultiDict
except ImportError:
    CIMultiDict = None
    MultiDict = None

try:
    from asyncpg.protocol.protocol import _create_record as Record
except ImportError:
    Record = None

try:
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    SQLAlchemyBase = declarative_base()
except ImportError:
    SQLAlchemyBase = None


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
    assert strip_ansi(stdout) == (
        '{\n'
        '    1: 2,\n'
        '    3: 4,\n'
        '}\n')
    assert stderr == ''


def test_colours():
    v = pformat({1: 2, 3: 4}, highlight=True)
    assert v.startswith('\x1b'), repr(v)
    v2 = strip_ansi(v)
    assert v2 == pformat({1: 2, 3: 4}), repr(v2)


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


def test_named_tuple():
    f = namedtuple('Foobar', ['foo', 'bar', 'spam'])
    v = pformat(f('x', 'y', 1))
    assert v == ("Foobar(\n"
                 "    foo='x',\n"
                 "    bar='y',\n"
                 "    spam=1,\n"
                 ")")


def test_generator_no_yield():
    pformat_ = PrettyFormat(yield_from_generators=False)
    v = pformat_((i for i in range(3)))
    assert v.startswith('<generator object test_generator_no_yield.<locals>.<genexpr> at ')


def test_str():
    pformat_ = PrettyFormat(width=12)
    v = pformat_(string.ascii_lowercase + '\n' + string.digits)
    print(repr(v))
    assert v == (
        "(\n"
        "    'abcde'\n"
        "    'fghij'\n"
        "    'klmno'\n"
        "    'pqrst'\n"
        "    'uvwxy'\n"
        "    'z\\n"
        "'\n"
        "    '01234'\n"
        "    '56789'\n"
        ")"
    )


def test_str_repr():
    pformat_ = PrettyFormat(repr_strings=True)
    v = pformat_(string.ascii_lowercase + '\n' + string.digits)
    assert v == "'abcdefghijklmnopqrstuvwxyz\\n0123456789'"


def test_bytes():
    pformat_ = PrettyFormat(width=12)
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


def test_bytearray():
    pformat_ = PrettyFormat(width=18)
    v = pformat_(bytearray(string.ascii_lowercase.encode()))
    assert v == """\
bytearray(
    b'abcdefghijk'
    b'lmnopqrstuv'
    b'wxyz'
)"""


def test_bytearray_short():
    v = pformat(bytearray(b'boo'))
    assert v == """\
bytearray(
    b'boo'
)"""


def test_map():
    v = pformat(map(str.strip, ['x', 'y ', ' z']))
    assert v == """\
map(
    'x',
    'y',
    'z',
)"""


def test_filter():
    v = pformat(filter(None, [1, 2, False, 3]))
    assert v == """\
filter(
    1,
    2,
    3,
)"""


def test_counter():
    c = Counter()
    c['x'] += 1
    c['x'] += 1
    c['y'] += 1
    v = pformat(c)
    assert v == """\
<Counter({
    'x': 2,
    'y': 1,
})>"""


def test_dataclass():
    @dataclass
    class FooDataclass:
        x: int
        y: List[int]

    f = FooDataclass(123, [1, 2, 3, 4])
    v = pformat(f)
    print(v)
    assert v == """\
FooDataclass(
    x=123,
    y=[
        1,
        2,
        3,
        4,
    ],
)"""


def test_nested_dataclasses():
    @dataclass
    class FooDataclass:
        x: int

    @dataclass
    class BarDataclass:
        a: float
        b: FooDataclass

    f = FooDataclass(123)
    b = BarDataclass(10.0, f)
    v = pformat(b)
    print(v)
    assert v == """\
BarDataclass(
    a=10.0,
    b=FooDataclass(
        x=123,
    ),
)"""


@pytest.mark.skipif(numpy is None, reason='numpy not installed')
def test_indent_numpy():
    v = pformat({'numpy test': numpy.array(range(20))})
    assert v == """{
    'numpy test': (
        array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16,
               17, 18, 19])
    ),
}"""


@pytest.mark.skipif(numpy is None, reason='numpy not installed')
def test_indent_numpy_short():
    v = pformat({'numpy test': numpy.array(range(10))})
    assert v == """{
    'numpy test': array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
}"""


def test_ordered_dict():
    v = pformat(OrderedDict([(1, 2), (3, 4), (5, 6)]))
    print(v)
    assert v == """\
OrderedDict([
    (1, 2),
    (3, 4),
    (5, 6),
])"""


def test_frozenset():
    v = pformat(frozenset(range(3)))
    print(v)
    assert v == """\
frozenset({
    0,
    1,
    2,
})"""


def test_deep_objects():
    f = namedtuple('Foobar', ['foo', 'bar', 'spam'])
    v = pformat((
        (
            f('x', 'y', OrderedDict([(1, 2), (3, 4), (5, 6)])),
            frozenset(range(3)),
            [1, 2, {1: 2}]
        ),
        {1, 2, 3}
    ))
    print(v)
    assert v == """\
(
    (
        Foobar(
            foo='x',
            bar='y',
            spam=OrderedDict([
                (1, 2),
                (3, 4),
                (5, 6),
            ]),
        ),
        frozenset({
            0,
            1,
            2,
        }),
        [
            1,
            2,
            {1: 2},
        ],
    ),
    {1, 2, 3},
)"""


def test_call_args():
    m = MagicMock()
    m(1, 2, 3, a=4)
    v = pformat(m.call_args)

    assert v == """\
_Call(
    _fields=(1, 2, 3),
    {'a': 4},
)"""


@pytest.mark.skipif(MultiDict is None, reason='MultiDict not installed')
def test_multidict():
    d = MultiDict({'a': 1, 'b': 2})
    d.add('b', 3)
    v = pformat(d)
    assert set(v.split('\n')) == {
        "<MultiDict({",
        "    'a': 1,",
        "    'b': 2,",
        "    'b': 3,",
        "})>",
    }


@pytest.mark.skipif(CIMultiDict is None, reason='MultiDict not installed')
def test_cimultidict():
    v = pformat(CIMultiDict({'a': 1, 'b': 2}))
    assert set(v.split('\n')) == {
        "<CIMultiDict({",
        "    'a': 1,",
        "    'b': 2,",
        "})>",
    }


def test_os_environ():
    v = pformat(os.environ)
    assert v.startswith('<_Environ({')
    for key in os.environ:
        assert f"    '{key}': " in v


class Foo:
    a = 1

    def __init__(self):
        self.b = 2
        self.c = 3


def test_dir():
    assert pformat(vars(Foo())) == (
        "{\n"
        "    'b': 2,\n"
        "    'c': 3,\n"
        "}"
    )


def test_instance_dict():
    assert pformat(Foo().__dict__) == (
        "{\n"
        "    'b': 2,\n"
        "    'c': 3,\n"
        "}"
    )


def test_class_dict():
    s = pformat(Foo.__dict__)
    assert s.startswith('<mappingproxy({\n')
    assert "    '__module__': 'tests.test_prettier',\n" in s
    assert "    'a': 1,\n" in s
    assert s.endswith('})>')


def test_dictlike():
    class Dictlike:
        _d = {'x': 4, 'y': 42, 3: None}

        def items(self):
            yield from self._d.items()

        def __getitem__(self, item):
            return self._d[item]

    assert pformat(Dictlike()) == (
        "<Dictlike({\n"
        "    'x': 4,\n"
        "    'y': 42,\n"
        "    3: None,\n"
        "})>"
    )


@pytest.mark.skipif(Record is None, reason='asyncpg not installed')
def test_asyncpg_record():
    r = Record({'a': 0, 'b': 1}, (41, 42))
    assert dict(r) == {'a': 41, 'b': 42}
    assert pformat(r) == (
        "<Record({\n"
        "    'a': 41,\n"
        "    'b': 42,\n"
        "})>"
    )


def test_dict_type():
    assert pformat(type({1: 2})) == "<class 'dict'>"


@pytest.mark.skipif(SQLAlchemyBase is None, reason='sqlalchemy not installed')
def test_sqlalchemy_object():
    class User(SQLAlchemyBase):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        nickname = Column(String)
    user = User()
    user.id = 1
    user.name = "Test"
    user.fullname = "Test For SQLAlchemy"
    user.nickname = "test"
    assert pformat(user) == (
        "User(\n"
        "    fullname='Test For SQLAlchemy',\n"
        "    id=1,\n"
        "    name='Test',\n"
        "    nickname='test',\n"
        ")"
    )
