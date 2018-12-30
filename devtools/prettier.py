import io
import os
import textwrap
from collections import OrderedDict
from collections.abc import Generator
from typing import Any, Union

from .ansi import isatty

try:
    import pygments
    from pygments.lexers import PythonLexer
    from pygments.formatters import Terminal256Formatter
except ImportError:  # pragma: no cover
    pyg_lexer = pyg_formatter = None
else:
    pyg_lexer, pyg_formatter = PythonLexer(), Terminal256Formatter(style='vim')

try:
    from multidict import MultiDict
except ImportError:
    MultiDict = None

__all__ = 'PrettyFormat', 'pformat', 'pprint'

DEFAULT_WIDTH = int(os.getenv('PY_DEVTOOLS_WIDTH', 120))
MISSING = object()


def env_true(var_name, alt=None):
    env = os.getenv(var_name, None)
    if env:
        return env.upper() in {'1', 'TRUE'}
    else:
        return alt


class FMT:
    __slots__ = '__prettier_formatting_value__'

    def __init__(self, v):
        self.__prettier_formatting_value__ = v


class PrettyFormat:
    def __init__(self,
                 indent_step=4,
                 indent_char=' ',
                 repr_strings=False,
                 simple_cutoff=10,
                 width=120,
                 yield_from_generators=True):
        self._indent_step = indent_step
        self._c = indent_char
        self._repr_strings = repr_strings
        self._repr_generators = not yield_from_generators
        self._simple_cutoff = simple_cutoff
        self._width = width
        self._type_lookup = [
            (dict, format_dict),
            ((str, bytes), self._format_str_bytes),
            (tuple, format_tuples),
            ((list, set, frozenset), format_list_like),
            (Generator, self._format_generators),
        ]

        if MultiDict:
            self._type_lookup.append((MultiDict, format_dict))

    def __call__(self, value: Any, *, indent: int = 0, highlight: bool = False):
        self._stream = io.StringIO()
        self._format(value, indent=indent)
        s = self._stream.getvalue()
        if highlight and pyg_lexer:
            # apparently highlight adds a trailing new line we don't want
            s = pygments.highlight(s, lexer=pyg_lexer, formatter=pyg_formatter).rstrip('\n')
        return s

    def _format(self, value: Any, indent: int):
        value_repr = repr(value)
        if len(value_repr) <= self._simple_cutoff and not isinstance(value, Generator):
            self._stream.write(value_repr)
        else:
            for t, func in self._type_lookup:
                if isinstance(value, t):
                    self._render(func(value=value, value_repr=value_repr, indent=indent), indent)
                    return
            self._render(self._format_raw(value=value, value_repr=value_repr, indent=indent), indent)

    def _render(self, gen, indent: int):
        prefix = False
        for v in gen:
            if isinstance(v, int):
                indent += v
                prefix = True
            else:
                if prefix:
                    self._stream.write('\n' + self._c * indent * self._indent_step)
                    prefix = False

                if hasattr(v, '__prettier_formatting_value__'):
                    self._format(v.__prettier_formatting_value__, indent)
                elif isinstance(v, str):
                    self._stream.write(v)
                else:
                    # shouldn't happen but will
                    self._stream.write(repr(v))

    def _format_str_bytes(self, value: Union[str, bytes], value_repr: str, indent: int):
        if self._repr_strings:
            yield value_repr
            return
        lines = list(self._wrap_lines(value, (indent + 1) * self._indent_step))
        if len(lines) > 1:
            yield '('
            yield 1
            for line in lines:
                yield repr(line)
                yield 0
            yield -1
            yield ')'
        else:
            yield value_repr

    def _wrap_lines(self, s, indent):
        width = self._width - indent - 3
        for line in s.splitlines(True):
            start = 0
            for pos in range(width, len(line), width):
                yield line[start:pos]
                start = pos
            yield line[start:]

    def _format_generators(self, value: Generator, value_repr, **kwargs):
        if self._repr_generators:
            yield value_repr
        else:
            yield '('
            yield 1
            for v in value:
                yield FMT(v)
                yield ','
                yield 0
            yield -1
            yield ')'

    def _format_raw(self, value: Any, value_repr: str, indent: int):
        lines = value_repr.splitlines(True)
        if len(lines) > 1 or (len(value_repr) + indent * self._indent_step) >= self._width:
            yield '('
            yield 1
            wrap_at = self._width - (indent + 1) * self._indent_step
            for line in lines:
                sub_lines = textwrap.wrap(line, wrap_at)
                for sline in sub_lines:
                    yield sline
                    yield 0
            yield -1
            yield ')'
        else:
            yield value_repr


def format_dict(value, **kwargs):
    open_, before_, split_, after_, close_ = '{', '', ': ', ',', '}'
    if isinstance(value, OrderedDict):
        open_, before_, split_, after_, close_ = 'OrderedDict([', '(', ', ', '),', '])'
    elif MultiDict and isinstance(value, MultiDict):
        open_, close_ = '<{}('.format(value.__class__.__name__), ')>'

    yield open_
    yield 1
    for k, v in value.items():
        yield before_
        yield FMT(k)
        yield split_
        yield FMT(v)
        yield after_
        yield 0
    yield -1
    yield close_


PARENTHESES_LOOKUP = [
    (list, '[', ']'),
    (set, '{', '}'),
    (frozenset, 'frozenset({', '})'),
]


def format_list_like(value: Union[list, tuple, set], **kwargs):
    open_, close_ = '(', ')'
    for t, *oc in PARENTHESES_LOOKUP:
        if isinstance(value, t):
            open_, close_ = oc
            break

    yield open_
    yield 1
    for v in value:
        yield FMT(v)
        yield ','
        yield 0
    yield -1
    yield close_


def format_tuples(value: tuple, **kwargs):
    fields = getattr(value, '_fields', None)
    if fields:
        # named tuple
        yield value.__class__.__name__ + '('
        yield 1
        for field, v in zip(fields, value):
            if field:  # field is falsy sometimes for odd things like call_args
                yield '{}='.format(field)
            yield FMT(v)
            yield ','
            yield 0
        yield -1
        yield ')'
    else:
        # normal tuples are just like other similar iterables
        yield from format_list_like(value, **kwargs)


pformat = PrettyFormat()
force_highlight = env_true('PY_DEVTOOLS_HIGHLIGHT', None)


def pprint(s, file=None):
    highlight = isatty(file) if force_highlight is None else force_highlight
    print(pformat(s, highlight=highlight), file=file, flush=True)
