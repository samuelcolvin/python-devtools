import io
import os
import textwrap
from collections import OrderedDict
from collections.abc import Generator
from typing import Any, Union
from unittest.mock import _Call as MockCall

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

PARENTHESES_LOOKUP = [
    (list, '[', ']'),
    (set, '{', '}'),
    (frozenset, 'frozenset({', '})'),
]
DEFAULT_WIDTH = int(os.getenv('PY_DEVTOOLS_WIDTH', 120))
MISSING = object()
PRETTY_KEY = '__prettier_formatted_value__'


def env_true(var_name, alt=None):
    env = os.getenv(var_name, None)
    if env:
        return env.upper() in {'1', 'TRUE'}
    else:
        return alt


def fmt(v):
    return {PRETTY_KEY: v}


class SkipPretty(Exception):
    pass


class PrettyFormat:
    def __init__(
        self,
        indent_step=4,
        indent_char=' ',
        repr_strings=False,
        simple_cutoff=10,
        width=120,
        yield_from_generators=True,
    ):
        self._indent_step = indent_step
        self._c = indent_char
        self._repr_strings = repr_strings
        self._repr_generators = not yield_from_generators
        self._simple_cutoff = simple_cutoff
        self._width = width
        self._type_lookup = [
            (dict, self._format_dict),
            ((str, bytes), self._format_str_bytes),
            (tuple, self._format_tuples),
            ((list, set, frozenset), self._format_list_like),
            (Generator, self._format_generators),
        ]

        if MultiDict:
            self._type_lookup.append((MultiDict, self._format_dict))

    def __call__(self, value: Any, *, indent: int = 0, indent_first: bool = False, highlight: bool = False):
        self._stream = io.StringIO()
        self._format(value, indent_current=indent, indent_first=indent_first)
        s = self._stream.getvalue()
        if highlight and pyg_lexer:
            # apparently highlight adds a trailing new line we don't want
            s = pygments.highlight(s, lexer=pyg_lexer, formatter=pyg_formatter).rstrip('\n')
        return s

    def _format(self, value: Any, indent_current: int, indent_first: bool):
        if indent_first:
            self._stream.write(indent_current * self._c)

        try:
            pretty_func = getattr(value, '__pretty__')
        except AttributeError:
            pass
        else:
            if hasattr(pretty_func, '__self__') and not isinstance(value, MockCall):
                try:
                    gen = pretty_func(fmt=fmt, skip_exc=SkipPretty)
                    self._render_pretty(gen, indent_current)
                except SkipPretty:
                    pass
                else:
                    return

        value_repr = repr(value)
        if len(value_repr) <= self._simple_cutoff and not isinstance(value, Generator):
            self._stream.write(value_repr)
        else:
            indent_new = indent_current + self._indent_step
            for t, func in self._type_lookup:
                if isinstance(value, t):
                    func(value, value_repr, indent_current, indent_new)
                    return
            self._format_raw(value, value_repr, indent_current, indent_new)

    def _render_pretty(self, gen, indent: int):
        prefix = False
        for v in gen:
            if isinstance(v, int) and v in {-1, 0, 1}:
                indent += v * self._indent_step
                prefix = True
            else:
                if prefix:
                    self._stream.write('\n' + self._c * indent)
                    prefix = False

                pretty_value = v.get(PRETTY_KEY, MISSING) if (isinstance(v, dict) and len(v) == 1) else MISSING
                if pretty_value is not MISSING:
                    self._format(pretty_value, indent, False)
                elif isinstance(v, str):
                    self._stream.write(v)
                else:
                    # shouldn't happen but will
                    self._stream.write(repr(v))

    def _format_dict(self, value: dict, value_repr: str, indent_current: int, indent_new: int):
        open_, before_, split_, after_, close_ = '{\n', indent_new * self._c, ': ', ',\n', '}'
        if isinstance(value, OrderedDict):
            open_, split_, after_, close_ = 'OrderedDict([\n', ', ', '),\n', '])'
            before_ += '('
        elif MultiDict and isinstance(value, MultiDict):
            open_, close_ = '<{}(\n'.format(value.__class__.__name__), ')>'

        self._stream.write(open_)
        for k, v in value.items():
            self._stream.write(before_)
            self._format(k, indent_new, False)
            self._stream.write(split_)
            self._format(v, indent_new, False)
            self._stream.write(after_)
        self._stream.write(indent_current * self._c + close_)

    def _format_list_like(self, value: Union[list, tuple, set], value_repr: str, indent_current: int, indent_new: int):
        open_, close_ = '(', ')'
        for t, *oc in PARENTHESES_LOOKUP:
            if isinstance(value, t):
                open_, close_ = oc
                break

        self._stream.write(open_ + '\n')
        for v in value:
            self._format(v, indent_new, True)
            self._stream.write(',\n')
        self._stream.write(indent_current * self._c + close_)

    def _format_tuples(self, value: tuple, value_repr: str, indent_current: int, indent_new: int):
        fields = getattr(value, '_fields', None)
        if fields:
            # named tuple
            self._stream.write(value.__class__.__name__ + '(\n')
            for field, v in zip(fields, value):
                self._stream.write(indent_new * self._c)
                if field:  # field is falsy sometimes for odd things like call_args
                    self._stream.write(str(field))
                    self._stream.write('=')
                self._format(v, indent_new, False)
                self._stream.write(',\n')
            self._stream.write(indent_current * self._c + ')')
        else:
            # normal tuples are just like other similar iterables
            return self._format_list_like(value, value_repr, indent_current, indent_new)

    def _format_str_bytes(self, value: Union[str, bytes], value_repr: str, indent_current: int, indent_new: int):
        if self._repr_strings:
            self._stream.write(value_repr)
        else:
            lines = list(self._wrap_lines(value, indent_new))
            if len(lines) > 1:
                self._stream.write('(\n')
                prefix = indent_new * self._c
                for line in lines:
                    self._stream.write(prefix + repr(line) + '\n')
                self._stream.write(indent_current * self._c + ')')
            else:
                self._stream.write(value_repr)

    def _wrap_lines(self, s, indent_new):
        width = self._width - indent_new - 3
        for line in s.splitlines(True):
            start = 0
            for pos in range(width, len(line), width):
                yield line[start:pos]
                start = pos
            yield line[start:]

    def _format_generators(self, value: Generator, value_repr: str, indent_current: int, indent_new: int):
        if self._repr_generators:
            self._stream.write(value_repr)
        else:
            self._stream.write('(\n')
            for v in value:
                self._format(v, indent_new, True)
                self._stream.write(',\n')
            self._stream.write(indent_current * self._c + ')')

    def _format_raw(self, value: Any, value_repr: str, indent_current: int, indent_new: int):
        lines = value_repr.splitlines(True)
        if len(lines) > 1 or (len(value_repr) + indent_current) >= self._width:
            self._stream.write('(\n')
            wrap_at = self._width - indent_new
            prefix = indent_new * self._c
            for line in lines:
                sub_lines = textwrap.wrap(line, wrap_at)
                for sline in sub_lines:
                    self._stream.write(prefix + sline + '\n')
            self._stream.write(indent_current * self._c + ')')
        else:
            self._stream.write(value_repr)


pformat = PrettyFormat()
force_highlight = env_true('PY_DEVTOOLS_HIGHLIGHT', None)


def pprint(s, file=None):
    highlight = isatty(file) if force_highlight is None else force_highlight
    print(pformat(s, highlight=highlight), file=file, flush=True)
