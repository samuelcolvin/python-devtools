import io
import os
from collections import OrderedDict
from collections.abc import Generator

from .utils import DataClassType, LaxMapping, SQLAlchemyClassType, env_true, isatty

__all__ = 'PrettyFormat', 'pformat', 'pprint'
MYPY = False
if MYPY:
    from typing import Any, Iterable, Union

PARENTHESES_LOOKUP = [
    (list, '[', ']'),
    (set, '{', '}'),
    (frozenset, 'frozenset({', '})'),
]
DEFAULT_WIDTH = int(os.getenv('PY_DEVTOOLS_WIDTH', 120))
MISSING = object()
PRETTY_KEY = '__prettier_formatted_value__'


def fmt(v):
    return {PRETTY_KEY: v}


class SkipPretty(Exception):
    pass


def get_pygments():
    try:
        import pygments
        from pygments.formatters import Terminal256Formatter
        from pygments.lexers import PythonLexer
    except ImportError:  # pragma: no cover
        return None, None, None
    else:
        return pygments, PythonLexer(), Terminal256Formatter(style='vim')


# common generator types (this is not exhaustive: things like chain are not include to avoid the import)
generator_types = Generator, map, filter, zip, enumerate


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
            (bytearray, self._format_bytearray),
            (generator_types, self._format_generator),
            # put this last as the check can be slow
            (LaxMapping, self._format_dict),
            (DataClassType, self._format_dataclass),
            (SQLAlchemyClassType, self._format_sqlalchemy_class),
        ]

    def __call__(self, value: 'Any', *, indent: int = 0, indent_first: bool = False, highlight: bool = False):
        self._stream = io.StringIO()
        self._format(value, indent_current=indent, indent_first=indent_first)
        s = self._stream.getvalue()
        pygments, pyg_lexer, pyg_formatter = get_pygments()
        if highlight and pygments:
            # apparently highlight adds a trailing new line we don't want
            s = pygments.highlight(s, lexer=pyg_lexer, formatter=pyg_formatter).rstrip('\n')
        return s

    def _format(self, value: 'Any', indent_current: int, indent_first: bool):
        if indent_first:
            self._stream.write(indent_current * self._c)

        try:
            pretty_func = getattr(value, '__pretty__')
        except AttributeError:
            pass
        else:
            # `pretty_func.__class__.__name__ == 'method'` should only be true for bound methods,
            # `hasattr(pretty_func, '__self__')` is more canonical but weirdly is true for unbound cython functions
            from unittest.mock import _Call as MockCall

            if pretty_func.__class__.__name__ == 'method' and not isinstance(value, MockCall):
                try:
                    gen = pretty_func(fmt=fmt, skip_exc=SkipPretty)
                    self._render_pretty(gen, indent_current)
                except SkipPretty:
                    pass
                else:
                    return

        value_repr = repr(value)
        if len(value_repr) <= self._simple_cutoff and not isinstance(value, generator_types):
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

    def _format_dict(self, value: 'Any', _: str, indent_current: int, indent_new: int):
        open_, before_, split_, after_, close_ = '{\n', indent_new * self._c, ': ', ',\n', '}'
        if isinstance(value, OrderedDict):
            open_, split_, after_, close_ = 'OrderedDict([\n', ', ', '),\n', '])'
            before_ += '('
        elif type(value) != dict:
            open_, close_ = f'<{value.__class__.__name__}({{\n', '})>'

        self._stream.write(open_)
        for k, v in value.items():
            self._stream.write(before_)
            self._format(k, indent_new, False)
            self._stream.write(split_)
            self._format(v, indent_new, False)
            self._stream.write(after_)
        self._stream.write(indent_current * self._c + close_)

    def _format_list_like(self, value: 'Union[list, tuple, set]', _: str, indent_current: int, indent_new: int):
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
            self._format_fields(value, zip(fields, value), indent_current, indent_new)
        else:
            # normal tuples are just like other similar iterables
            return self._format_list_like(value, value_repr, indent_current, indent_new)

    def _format_str_bytes(self, value: 'Union[str, bytes]', value_repr: str, indent_current: int, indent_new: int):
        if self._repr_strings:
            self._stream.write(value_repr)
        else:
            lines = list(self._wrap_lines(value, indent_new))
            if len(lines) > 1:
                self._str_lines(lines, indent_current, indent_new)
            else:
                self._stream.write(value_repr)

    def _str_lines(self, lines: 'Iterable[str]', indent_current: int, indent_new: int) -> None:
        self._stream.write('(\n')
        prefix = indent_new * self._c
        for line in lines:
            self._stream.write(prefix + repr(line) + '\n')
        self._stream.write(indent_current * self._c + ')')

    def _wrap_lines(self, s, indent_new) -> 'Generator[str, None, None]':
        width = self._width - indent_new - 3
        for line in s.splitlines(True):
            start = 0
            for pos in range(width, len(line), width):
                yield line[start:pos]
                start = pos
            yield line[start:]

    def _format_generator(self, value: Generator, value_repr: str, indent_current: int, indent_new: int):
        if self._repr_generators:
            self._stream.write(value_repr)
        else:
            name = value.__class__.__name__
            if name == 'generator':
                # no name if the name is just "generator"
                self._stream.write('(\n')
            else:
                self._stream.write(f'{name}(\n')
            for v in value:
                self._format(v, indent_new, True)
                self._stream.write(',\n')
            self._stream.write(indent_current * self._c + ')')

    def _format_bytearray(self, value: 'Any', _: str, indent_current: int, indent_new: int):
        self._stream.write('bytearray')
        lines = self._wrap_lines(bytes(value), indent_new)
        self._str_lines(lines, indent_current, indent_new)

    def _format_dataclass(self, value: 'Any', _: str, indent_current: int, indent_new: int):
        from dataclasses import asdict

        self._format_fields(value, asdict(value).items(), indent_current, indent_new)

    def _format_sqlalchemy_class(self, value: 'Any', _: str, indent_current: int, indent_new: int):
        fields = {}
        for field in dir(value):
            if not field.startswith('_') and field not in ['metadata', 'registry']:
                data = getattr(value, field)
                try:
                    fields[field] = data
                except TypeError:
                    pass

        self._format_fields(value, fields.items(), indent_current, indent_new)

    def _format_raw(self, _: 'Any', value_repr: str, indent_current: int, indent_new: int):
        lines = value_repr.splitlines(True)
        if len(lines) > 1 or (len(value_repr) + indent_current) >= self._width:
            self._stream.write('(\n')
            wrap_at = self._width - indent_new
            prefix = indent_new * self._c

            from textwrap import wrap

            for line in lines:
                sub_lines = wrap(line, wrap_at)
                for sline in sub_lines:
                    self._stream.write(prefix + sline + '\n')
            self._stream.write(indent_current * self._c + ')')
        else:
            self._stream.write(value_repr)

    def _format_fields(self, value, fields, indent_current: int, indent_new: int):
        self._stream.write(f'{value.__class__.__name__}(\n')
        for field, v in fields:
            self._stream.write(indent_new * self._c)
            if field:  # field is falsy sometimes for odd things like call_args
                self._stream.write(str(field))
                self._stream.write('=')
            self._format(v, indent_new, False)
            self._stream.write(',\n')
        self._stream.write(indent_current * self._c + ')')


pformat = PrettyFormat()
force_highlight = env_true('PY_DEVTOOLS_HIGHLIGHT', None)


def pprint(s, file=None):
    highlight = isatty(file) if force_highlight is None else force_highlight
    print(pformat(s, highlight=highlight), file=file, flush=True)
