from collections.abc import Callable, Generator
from importlib.util import find_spec
from typing import Any

import pytest

from devtools import pformat


def test_simple():
    class CustomCls:
        def __pretty__(self, fmt: Callable[[Any], Any], **kwargs: Any) -> Generator[Any, None, None]:
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
    assert (
        v
        == """\
Thing(
    [],
    [0],
    [0, 1],
)"""
    )


def test_skip():
    class CustomCls:
        def __pretty__(
            self, fmt: Callable[[Any], Any], skip_exc: type[Exception], **kwargs: Any
        ) -> Generator[Any, None, None]:
            raise skip_exc()
            yield 'Thing()'

        def __repr__(self) -> str:
            return '<CustomCls repr>'

    my_cls = CustomCls()
    v = pformat(my_cls)
    assert v == '<CustomCls repr>'


def test_yield_other():
    class CustomCls:
        def __pretty__(self, fmt: Callable[[Any], Any], **kwargs: Any) -> Generator[Any, None, None]:
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
        def __pretty__(self, fmt: Callable[[Any], Any], **kwargs: Any) -> Generator[Any, None, None]:
            yield 'xxx'

    assert pformat(Foobar()) == 'xxx'
    assert pformat(Foobar) == "<class 'tests.test_custom_pretty.test_pretty_class.<locals>.Foobar'>"


@pytest.mark.skipif(find_spec('pydantic') is None, reason='pydantic not installed')
def test_pydantic_pretty():
    from pydantic import BaseModel

    class MyModel(BaseModel):
        foobar: int = 1

    assert pformat(MyModel()) == 'MyModel(\n    foobar=1,\n)'
    assert pformat(MyModel) == "<class 'tests.test_custom_pretty.test_pydantic_pretty.<locals>.MyModel'>"
