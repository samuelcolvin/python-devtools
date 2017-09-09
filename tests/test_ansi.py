import pytest

from devtools.ansi import sprint, style


def test_colorize():
    v = style('hello', style.red)
    assert v == '\x1b[31mhello\x1b[0m', repr(v)


def test_no_reset():
    v = style('hello', style.bold, reset=False)
    assert v == '\x1b[1mhello', repr(v)


def test_style_str():
    v = style('hello', 'red')
    assert v == '\x1b[31mhello\x1b[0m', repr(v)


def test_invalid_style_str():
    with pytest.raises(ValueError) as exc_info:
        style('x', 'mauve')
    assert exc_info.value.args[0] == 'invalid style "mauve"'


def test_print(capsys):
    sprint('hello', style.green)
    stdout, stderr = capsys.readouterr()
    assert stdout == '\x1b[32mhello\x1b[0m\n', repr(stdout)
    assert stderr == ''


def test_get_styles():
    assert style.styles['bold'] == 1
    assert style.styles['un_bold'] == 22


def test_repr():
    assert repr(style) == '<pseudo function style(text, *styles)>'
    assert repr(style.red) == '<Style.red: 31>'


def test_str():
    assert str(style) == '<pseudo function style(text, *styles)>'
    assert str(style.red) == 'Style.red'
