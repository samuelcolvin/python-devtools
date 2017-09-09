import io

import pytest

from devtools.ansi import sformat, sprint


def test_colours():
    v = sformat('hello', sformat.red)
    assert v == '\x1b[31mhello\x1b[0m'


def test_no_reset():
    v = sformat('hello', sformat.bold, reset=False)
    assert v == '\x1b[1mhello'


def test_combine_styles():
    v = sformat('hello', sformat.red, sformat.bold)
    assert v == '\x1b[31;1mhello\x1b[0m'


def test_no_styles():
    v = sformat('hello')
    assert v == 'hello\x1b[0m'


def test_style_str():
    v = sformat('hello', 'red')
    assert v == '\x1b[31mhello\x1b[0m'


def test_non_str_input():
    v = sformat(12.2, sformat.yellow, sformat.italic)
    assert v == '\x1b[33;3m12.2\x1b[0m'


def test_invalid_style_str():
    with pytest.raises(ValueError) as exc_info:
        sformat('x', 'mauve')
    assert exc_info.value.args[0] == 'invalid style "mauve"'


def test_print_not_tty():
    stream = io.StringIO()
    sprint('hello', sprint.green, file=stream)
    out = stream.getvalue()
    assert out == 'hello\n'


def test_print_is_tty():
    class TTYStream(io.StringIO):
        def isatty(self):
            return True

    stream = TTYStream()
    sprint('hello', sprint.green, file=stream)
    out = stream.getvalue()
    assert out == '\x1b[32mhello\x1b[0m\n', repr(out)


def test_print_tty_error():
    class TTYStream(io.StringIO):
        def isatty(self):
            raise RuntimeError('boom')

    stream = TTYStream()
    sprint('hello', sformat.green, file=stream)
    out = stream.getvalue()
    assert out == 'hello\n'


def test_get_styles():
    assert sformat.styles['bold'] == 1
    assert sformat.styles['not_bold'] == 22


def test_repr_str():
    assert repr(sformat) == '<pseudo function sformat(text, *styles)>'
    assert repr(sformat.red) == '<Style.red: 31>'

    assert str(sformat) == '<pseudo function sformat(text, *styles)>'
    assert str(sformat.red) == 'Style.red'

    assert repr(sprint) == '<pseudo function sprint(text, *styles)>'
    assert str(sprint) == '<pseudo function sprint(text, *styles)>'
