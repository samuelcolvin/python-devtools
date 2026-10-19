from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import pytest

from devtools import Debug
from devtools.prettier import PrettyFormat, pformat


def test_recursive_dict():
    value: dict[str, Any] = {'before': 1}
    value['self'] = value
    value['after'] = 2
    expected = "{\n    'before': 1,\n    'self': <Recursion on dict>,\n    'after': 2,\n}"
    assert pformat(value) == expected
    assert pformat(value) == expected


@pytest.mark.parametrize('cutoff', [0, 10])
def test_recursive_list(cutoff: int):
    value: list[Any] = [1, 2]
    value.append(value)
    assert PrettyFormat(simple_cutoff=cutoff)(value) == '[\n    1,\n    2,\n    <Recursion on list>,\n]'


@pytest.mark.parametrize('cutoff', [0, 10])
def test_short_recursive_list(cutoff: int):
    value: list[Any] = []
    value.append(value)
    expected = '[\n    <Recursion on list>,\n]' if cutoff == 0 else '[[...]]'
    assert PrettyFormat(simple_cutoff=cutoff)(value) == expected


@pytest.mark.parametrize('cutoff', [0, 100])
def test_compact_recursive_dict(cutoff: int):
    value: dict[str, Any] = {}
    value['self'] = value
    expected = "{\n    'self': <Recursion on dict>,\n}" if cutoff == 0 else "{'self': {...}}"
    assert PrettyFormat(simple_cutoff=cutoff)(value) == expected


def test_mutually_recursive_containers():
    value: dict[str, Any] = {}
    value['child'] = [value, 1]
    assert pformat(value) == "{\n    'child': [\n        <Recursion on dict>,\n        1,\n    ],\n}"


@pytest.mark.parametrize('slots', [False, True])
def test_recursive_dataclass(slots: bool):
    @dataclass(slots=slots)
    class Node:
        child: Any = None

    value = Node()
    value.child = value
    assert pformat(value) == 'Node(\n    child=<Recursion on Node>,\n)'


def test_recursive_pretty():
    class Pretty:
        def __pretty__(self, fmt: Callable[[Any], Any], skip_exc: type[Exception]) -> Iterator[Any]:
            yield 'Pretty('
            yield fmt(self)
            yield ')'

    assert pformat(Pretty()) == 'Pretty(<Recursion on Pretty>)'


def test_recursive_generator():
    def generate() -> Iterator[Any]:
        yield value
        yield 1

    value = generate()
    assert pformat(value) == '(\n    <Recursion on generator>,\n    1,\n)'


def test_recursive_reentrant_repr():
    formatter = PrettyFormat()

    class Reentrant:
        def __repr__(self) -> str:
            return formatter(self)

    assert formatter(Reentrant()) == '<Recursion on Reentrant>'
    assert formatter(1) == '1'


def test_shared_child_is_not_recursive():
    child = {'value': 1}
    assert PrettyFormat(simple_cutoff=0)([child, child]) == (
        "[\n    {\n        'value': 1,\n    },\n    {\n        'value': 1,\n    },\n]"
    )


def test_formatting_error_does_not_mark_value_as_recursive():
    formatter = PrettyFormat()

    class Broken:
        fail = True

        def __repr__(self) -> str:
            if self.fail:
                raise ValueError('broken repr')
            return 'recovered'

    value = Broken()
    with pytest.raises(ValueError, match='broken repr'):
        formatter(value)
    value.fail = False
    assert formatter(value) == 'recovered'


def test_debug_recursive_value():
    value: dict[str, Any] = {'before': 1}
    value['self'] = value
    output = str(Debug(highlight=False).format(value))
    assert "'before': 1" in output
    assert "'self': <Recursion on dict>" in output
