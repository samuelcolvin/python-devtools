import io

import pytest

from devtools.ansi import sprint, style


def test_colorize():
    v = style('hello', style.red)
    assert v == '\x1b[31mhello\x1b[0m'


def test_no_reset():
    v = style('hello', style.bold, reset=False)
    assert v == '\x1b[1mhello'


def test_combine_styles():
    v = style('hello', style.red, style.bold)
    assert v == '\x1b[31;1mhello\x1b[0m'


def test_no_styles():
    v = style('hello')
    assert v == 'hello\x1b[0m'


def test_style_str():
    v = style('hello', 'red')
    assert v == '\x1b[31mhello\x1b[0m'


def test_invalid_style_str():
    with pytest.raises(ValueError) as exc_info:
        style('x', 'mauve')
    assert exc_info.value.args[0] == 'invalid style "mauve"'


def test_print_not_tty():
    stream = io.StringIO()
    sprint('hello', style.green, file=stream)
    out = stream.getvalue()
    assert out == 'hello\n'


def test_print_is_tty():
    class TTYStream(io.StringIO):
        def isatty(self):
            return True

    stream = TTYStream()
    sprint('hello', style.green, file=stream)
    out = stream.getvalue()
    assert out == '\x1b[32mhello\x1b[0m\n', repr(out)


def test_print_tty_error():
    class TTYStream(io.StringIO):
        def isatty(self):
            raise RuntimeError('boom')

    stream = TTYStream()
    sprint('hello', style.green, file=stream)
    out = stream.getvalue()
    assert out == 'hello\n'


def test_get_styles():
    assert style.styles['bold'] == 1
    assert style.styles['un_bold'] == 22


def test_repr():
    assert repr(style) == '<pseudo function style(text, *styles)>'
    assert repr(style.red) == '<Style.red: 31>'


def test_str():
    assert str(style) == '<pseudo function style(text, *styles)>'
    assert str(style.red) == 'Style.red'
