from enum import IntEnum

_ansi_template = '\033[{}m'


class Style(IntEnum):
    """
    Heavily borrowed from https://github.com/pallets/click/blob/6.7/click/termui.py

    Italic added and generally modernised improved.
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

    def __call__(self, text: str, *styles, reset: bool=True):
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
        parts = []
        for s in styles:
            if not isinstance(s, self.__class__):
                try:
                    s = self.styles[s]
                except KeyError:
                    raise ValueError('invalid style "{}"'.format(s))
            parts.append(_ansi_template.format(s))
        parts.append(text)
        if reset:
            parts.append(_ansi_template.format(self.reset))
        return ''.join(parts)

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


style = Style(-1)


def sprint(text, *styles, reset=True, flush=True, **print_kwargs):
    print(style(text, *styles, reset=reset), flush=flush, **print_kwargs)
