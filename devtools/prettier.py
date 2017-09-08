import io
import textwrap
import collections
from typing import Any


PARENTHESES_LOOKUP = [
    (list, '[', ']'),
    (set, '{', '}'),
]


class PrettyFormat:
    def __init__(self,
                 indent_step=4,
                 indent_char=' ',
                 repr_strings=False,
                 yield_from_generators=True):
        # TODO colours
        self._indent_step = indent_step
        self._c = indent_char
        self._repr_strings = repr_strings
        self._repr_generators = not yield_from_generators
        self._type_lookup = [
            (dict, self._format_dict),
            ((tuple, list, set), self._format_list_like),
            (str, self._format_str),
            (collections.Generator, self._format_generators),
        ]

    def __call__(self, value: Any, *, indent_current: int=0):
        self._stream = io.StringIO()
        self._format(value, indent_current=indent_current, indent_first=True)
        return self._stream.getvalue()

    def _format(self, value: Any, indent_current: int, indent_first: bool):
        if indent_first:
            self._stream.write(indent_current * self._c)

        indent_new = indent_current + self._indent_step
        for t, func in self._type_lookup:
            if isinstance(value, t):
                func(value, indent_current, indent_new)
                return

        value_s = repr(value)
        if '\n' in value_s:
            value_s = textwrap.indent(value_s, indent_new * self._c).lstrip(' ')
        self._stream.write(value_s)

    def _format_dict(self, value, indent_current, indent_new):
        self._stream.write('{\n')
        for k, v in value.items():
            self._format(k, indent_new, True)
            self._stream.write(': ')
            self._format(v, indent_new, False)
            self._stream.write(',\n')
        self._stream.write(indent_current * self._c + '}')

    def _format_list_like(self, value, indent_current, indent_new):
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

    def _format_str(self, value, indent_current, indent_new):
        if self._repr_strings:
            self._stream.write(repr(value))
        else:
            lines = value.splitlines(True)
            if len(lines) > 1:
                self._stream.write('(\n')
                prefix = indent_new * self._c
                for line in lines:
                    self._stream.write(prefix + repr(line) + '\n')
                self._stream.write(indent_current * self._c + ')')
            else:
                self._stream.write(repr(value))

    def _format_generators(self, value, indent_current, indent_new):
        if self._repr_generators:
            self._stream.write(repr(value))
        else:
            self._stream.write('(\n')
            for v in value:
                self._format(v, indent_new, True)
                self._stream.write(',\n')
            self._stream.write(indent_current * self._c + ')')


pformat = PrettyFormat()


def pprint(s):
    print(pformat(s), flush=True)
