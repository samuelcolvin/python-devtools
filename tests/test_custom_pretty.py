from devtools import pformat


def test_simple():
    class CustomCls:
        def __pretty__(self, fmt, **kwargs):
            yield 'Thing('
            yield 1
            for i in range(3):
                yield fmt(list(range(i)))
                yield ','
                yield 0
            yield -1
            yield ')'

    my_cls = CustomCls()

    v = pformat(my_cls)
    assert v == """\
Thing(
    [],
    [0],
    [0, 1],
)"""


def test_skip():
    class CustomCls:
        def __pretty__(self, fmt, skip_exc, **kwargs):
            raise skip_exc()
            yield 'Thing()'

        def __repr__(self):
            return '<CustomCls repr>'

    my_cls = CustomCls()
    v = pformat(my_cls)
    assert v == '<CustomCls repr>'


def test_yield_other():
    class CustomCls:
        def __pretty__(self, fmt, **kwargs):
            yield fmt('xxx')
            yield 123

    my_cls = CustomCls()
    v = pformat(my_cls)
    assert v == "'xxx'123"


def test_pretty_not_func():
    class Foobar:
        __pretty__ = 1

    assert '<locals>.Foobar object' in pformat(Foobar())


def test_pretty_class():
    class Foobar:
        def __pretty__(self, fmt, **kwargs):
            yield 'xxx'

    assert pformat(Foobar()) == 'xxx'
    assert pformat(Foobar).endswith(".test_pretty_class.<locals>.Foobar'>")
