import re
import sys
from enum import IntEnum
from typing import Any

_ansi_template = '\033[{}m'
_ansi_re = re.compile('\033\[((?:\d|;)*)([a-zA-Z])')

__all__ = ['sformat', 'sprint']


def isatty(stream=None):
    stream = stream or sys.stdout
    try:
        return stream.isatty()
    except Exception:
        return False


def strip_ansi(value):
    return _ansi_re.sub('', value)


class Style(IntEnum):
    """
    Heavily borrowed from https://github.com/pallets/click/blob/6.7/click/termui.py

    Italic added, multiple ansi codes condensed into one block and generally modernised.
    """
    reset = 0

    bold = 1
    un_bold = 22

    dim = 2
    un_dim = 22

    italic = 3
    un_italic = 23

    underline = 4
    un_underline = 24

    blink = 5
    un_blink = 25

    reverse = 7
    un_reverse = 27

    # foreground colours
    black = 30
    red = 31
    green = 32
    yellow = 33
    blue = 34
    magenta = 35
    cyan = 36
    white = 37
    fg_reset = 38

    # background colours
    bg_black = 40
    bg_red = 41
    bg_green = 42
    bg_yellow = 43
    bg_blue = 44
    bg_magenta = 45
    bg_cyan = 46
    bg_white = 47
    bg_reset = 48

    # this is a meta value used for the "Style" instance which is the "style" function
    function = -1

    def __call__(self, text: Any, *styles, reset: bool=True):
        """
        Styles a text with ANSI styles and returns the new string.

        By default the styling is cleared at the end of the string, this can be prevented with``reset=False``.

        Examples::

            print(style('Hello World!', style.green))
            print(style('ATTENTION!', style.bg_magenta))
            print(style('Some things', style.reverse, style.bold))

        Supported color names:

        * ``black`` (might be a gray)
        * ``red``
        * ``green``
        * ``yellow`` (might be an orange)
        * ``blue``
        * ``magenta``
        * ``cyan``
        * ``white`` (might be light gray)
        * ``reset`` (reset the color code only)

        :param text: the string to style with ansi codes.
        :param *styles: zero or more styles to apply to the text, should be either style instances or strings
                        matching style names.
        :param reset: by default a reset-all code is added at the end of the
                      string which means that styles do not carry over.  This
                      can be disabled to compose styles.
        """
        codes = []
        for s in styles:
            if not isinstance(s, self.__class__):
                try:
                    s = self.styles[s]
                except KeyError:
                    raise ValueError('invalid style "{}"'.format(s))
            codes.append(str(s.value))

        if codes:
            r = _ansi_template.format(';'.join(codes)) + str(text)
        else:
            r = str(text)

        if reset:
            r += _ansi_template.format(self.reset)
        return r

    @property
    def styles(self):
        return self.__class__.__members__

    def __repr__(self):
        if self == self.function:
            return '<pseudo function style(text, *styles)>'
        else:
            return super().__repr__()

    def __str__(self):
        if self == self.function:
            return repr(self)
        else:
            return super().__str__()


sformat = Style(-1)


def sprint(text, *styles, reset=True, flush=True, file=None, **print_kwargs):
    if isatty(file):
        text = sformat(text, *styles, reset=reset)
    print(text, flush=flush, file=file, **print_kwargs)
