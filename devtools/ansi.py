from enum import IntEnum

from .utils import isatty

_ansi_template = '\033[{}m'

__all__ = 'sformat', 'sprint'

MYPY = False
if MYPY:
    from typing import Any, Union


def strip_ansi(value):
    import re

    return re.sub('\033\\[((?:\\d|;)*)([a-zA-Z])', '', value)


class Style(IntEnum):
    reset = 0

    bold = 1
    not_bold = 22

    dim = 2
    not_dim = 22

    italic = 3
    not_italic = 23

    underline = 4
    not_underline = 24

    blink = 5
    not_blink = 25

    reverse = 7
    not_reverse = 27

    strike_through = 9
    not_strike_through = 29

    # foreground colours
    black = 30
    red = 31
    green = 32
    yellow = 33
    blue = 34
    magenta = 35
    cyan = 36
    white = 37

    # background colours
    bg_black = 40
    bg_red = 41
    bg_green = 42
    bg_yellow = 43
    bg_blue = 44
    bg_magenta = 45
    bg_cyan = 46
    bg_white = 47

    # this is a meta value used for the "Style" instance which is the "style" function
    function = -1

    def __call__(self, input: 'Any', *styles: 'Style', reset: bool = True, apply: bool = True) -> str:
        """
        Styles text with ANSI styles and returns the new string.

        By default the styling is cleared at the end of the string, this can be prevented with``reset=False``.

        Examples::

            print(sformat('Hello World!', sformat.green))
            print(sformat('ATTENTION!', sformat.bg_magenta))
            print(sformat('Some things', sformat.reverse, sformat.bold))

        :param input: the object to style with ansi codes.
        :param *styles: zero or more styles to apply to the text, should be either style instances or strings
                        matching style names.
        :param reset: if False the ansi reset code is not appended to the end of the string
        :param: apply: if False no ansi codes are applied
        """
        text = str(input)
        if not apply:
            return text
        codes = []
        for s in styles:
            # raw ints are allowed
            if not isinstance(s, self.__class__) and not isinstance(s, int):
                try:
                    s = self.styles[s]
                except KeyError:
                    raise ValueError('invalid style "{}"'.format(s))
            codes.append(_style_as_int(s.value))

        if codes:
            r = _ansi_template.format(';'.join(codes)) + text
        else:
            r = text

        if reset:
            r += _ansi_template.format(_style_as_int(self.reset))
        return r

    @property
    def styles(self):
        return self.__class__.__members__

    def __repr__(self):
        if self == self.function:
            return '<pseudo function sformat(text, *styles)>'
        else:
            return super().__repr__()

    def __str__(self):
        if self == self.function:
            return repr(self)
        else:
            return super().__str__()


def _style_as_int(v: 'Union[Style, int]') -> str:
    if isinstance(v, Style):
        return str(v.value)
    else:
        return str(v)


sformat = Style(-1)


class StylePrint:
    """
    Annoyingly enums do not allow inheritance, a lazy design mistake, this is an ugly work around
    for that mistake.
    """

    def __call__(self, input, *styles, reset=True, flush=True, file=None, **print_kwargs):
        text = sformat(input, *styles, reset=reset, apply=isatty(file))
        print(text, flush=flush, file=file, **print_kwargs)

    def __getattr__(self, item):
        return getattr(sformat, item)

    def __repr__(self):
        return '<pseudo function sprint(text, *styles)>'


sprint = StylePrint()
