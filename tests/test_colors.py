import io

import pytest

import devtools.prettier
from devtools import Debug, pformat, pprint, sprint


@pytest.mark.parametrize('printer', ['debug', 'pprint'])
@pytest.mark.parametrize('tty', [False, True])
@pytest.mark.parametrize('no_color', [None, '', '1', '0', 'false'])
def test_no_color_default(monkeypatch: pytest.MonkeyPatch, printer: str, tty: bool, no_color: str | None):
    monkeypatch.delenv('PY_DEVTOOLS_HIGHLIGHT', raising=False)
    monkeypatch.setattr(devtools.prettier, 'force_highlight', None)
    if no_color is None:
        monkeypatch.delenv('NO_COLOR', raising=False)
    else:
        monkeypatch.setenv('NO_COLOR', no_color)
    output = io.StringIO()
    monkeypatch.setattr(output, 'isatty', lambda: tty)
    monkeypatch.setattr('devtools.utils.activate_win_color', lambda: True)

    if printer == 'debug':
        Debug()(1, file_=output)
    else:
        pprint(1, file=output)

    assert ('\x1b[' in output.getvalue()) is (tty and not no_color)


@pytest.mark.parametrize('printer', ['debug', 'pprint'])
@pytest.mark.parametrize('tty', [False, True])
@pytest.mark.parametrize('highlight', [False, True])
def test_no_color_config_override(monkeypatch: pytest.MonkeyPatch, printer: str, tty: bool, highlight: bool):
    monkeypatch.setenv('NO_COLOR', '1')
    monkeypatch.setenv('PY_DEVTOOLS_HIGHLIGHT', str(highlight))
    monkeypatch.setattr(devtools.prettier, 'force_highlight', highlight)
    output = io.StringIO()
    monkeypatch.setattr(output, 'isatty', lambda: tty)

    if printer == 'debug':
        Debug()(1, file_=output)
    else:
        pprint(1, file=output)

    assert ('\x1b[' in output.getvalue()) is highlight


@pytest.mark.parametrize('highlight', [False, True])
@pytest.mark.parametrize('tty', [False, True])
def test_no_color_explicit_debug_override(monkeypatch: pytest.MonkeyPatch, highlight: bool, tty: bool):
    monkeypatch.setenv('NO_COLOR', '1')
    monkeypatch.setenv('PY_DEVTOOLS_HIGHLIGHT', str(not highlight))
    output = io.StringIO()
    monkeypatch.setattr(output, 'isatty', lambda: tty)

    Debug(highlight=highlight)(1, file_=output)

    assert ('\x1b[' in output.getvalue()) is highlight


def test_no_color_explicit_pformat_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('NO_COLOR', '1')
    assert '\x1b[' not in pformat(1)
    assert '\x1b[' in pformat(1, highlight=True)


def test_pprint_highlight_config_snapshot(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.setenv('PY_DEVTOOLS_HIGHLIGHT', 'True')
    monkeypatch.setattr(devtools.prettier, 'force_highlight', None)
    output = io.StringIO()
    monkeypatch.setattr(output, 'isatty', lambda: False)

    pprint(1, file=output)

    assert output.getvalue() == '1\n'


@pytest.mark.parametrize('no_color', [None, '', '1'])
def test_sprint_no_color(monkeypatch: pytest.MonkeyPatch, no_color: str | None):
    if no_color is None:
        monkeypatch.delenv('NO_COLOR', raising=False)
    else:
        monkeypatch.setenv('NO_COLOR', no_color)
    output = io.StringIO()
    monkeypatch.setattr(output, 'isatty', lambda: True)

    sprint('hello', sprint.green, file=output)

    assert ('\x1b[' in output.getvalue()) is (not no_color)
