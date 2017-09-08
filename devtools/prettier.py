import collections
import io
import textwrap
from typing import Any, Generator, Union

try:
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatters import Terminal256Formatter
except ImportError:  # pragma: no cover
    pyg_lexer = pyg_formatter = None
else:
    pyg_lexer, pyg_formatter = PythonLexer(), Terminal256Formatter(style='vim')

PARENTHESES_LOOKUP = [
    (list, '[', ']'),
    (set, '{', '}'),
]


class PrettyFormat:
    def __init__(self,
                 colorize=False,
                 indent_step=4,
                 indent_char=' ',
                 repr_strings=False,
                 simple_cuttoff=10,
                 max_width=120,
                 yield_from_generators=True):
        # TODO colours
        self._colorize = colorize
        self._indent_step = indent_step
        self._c = indent_char
        self._repr_strings = repr_strings
        self._repr_generators = not yield_from_generators
        self._simple_cuttoff = simple_cuttoff
        self._max_width = max_width
        self._type_lookup = [
            (dict, self._format_dict),
            ((tuple, list, set), self._format_list_like),
            (str, self._format_str),
            (bytes, self._format_bytes),
            (collections.Generator, self._format_generators),
        ]

    def __call__(self, value: Any, *, indent_current: int=0):
        self._stream = io.StringIO()
        self._format(value, indent_current=indent_current, indent_first=True)
        s = self._stream.getvalue()
        if self._colorize and pyg_lexer:
            s = highlight(s, lexer=pyg_lexer, formatter=pyg_formatter)
        return s

    def _format(self, value: Any, indent_current: int, indent_first: bool):
        if indent_first:
            self._stream.write(indent_current * self._c)

        value_repr = repr(value)
        if len(value_repr) <= self._simple_cuttoff and not isinstance(value, collections.Generator):
            self._stream.write(value_repr)
        else:
            indent_new = indent_current + self._indent_step
            for t, func in self._type_lookup:
                if isinstance(value, t):
                    func(value, value_repr, indent_current, indent_new)
                    return
            self._format_raw(value, value_repr, indent_current, indent_new)

    def _format_dict(self, value: dict, value_repr: str, indent_current: int, indent_new: int):
        self._stream.write('{\n')
        for k, v in value.items():
            self._format(k, indent_new, True)
            self._stream.write(': ')
            self._format(v, indent_new, False)
            self._stream.write(',\n')
        self._stream.write(indent_current * self._c + '}')

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

    def _format_str(self, value: str, value_repr: str, indent_current: int, indent_new: int):
        if self._repr_strings:
            self._stream.write(value_repr)
        else:
            lines = value.splitlines(True)
            if len(lines) > 1:
                self._stream.write('(\n')
                prefix = indent_new * self._c
                for line in lines:
                    self._stream.write(prefix + repr(line) + '\n')
                self._stream.write(indent_current * self._c + ')')
            else:
                self._stream.write(value_repr)

    def _format_bytes(self, value: bytes, value_repr: str, indent_current: int, indent_new: int):
        wrap = self._max_width - indent_new - 3
        if len(value) < wrap:
            self._stream.write(value_repr)
        else:
            self._stream.write('(\n')
            prefix = indent_new * self._c
            start, end = 0, wrap
            while start < len(value):
                line = value[start:end]
                self._stream.write(prefix + repr(line) + '\n')
                start = end
                end += wrap
            self._stream.write(indent_current * self._c + ')')

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
        if len(lines) > 1 or (len(value_repr) + indent_current) >= self._max_width:
            self._stream.write('(\n')
            wrap_at = self._max_width - indent_new
            prefix = indent_new * self._c
            for line in lines:
                sub_lines = textwrap.wrap(line, wrap_at)
                for sline in sub_lines:
                    self._stream.write(prefix + sline + '\n')
            self._stream.write(indent_current * self._c + ')')
        else:
            self._stream.write(value_repr)


pformat = PrettyFormat()
_ppformat = PrettyFormat(colorize=True)


def pprint(s):
    print(_ppformat(s), flush=True)
