import sys

import pytest

import devtools.utils
from devtools.utils import env_bool, env_true, use_highlight


def test_env_true():
    assert env_true('PATH') is False
    assert env_true('DOES_NOT_EXIST') is None


def test_env_bool(monkeypatch):
    assert env_bool(False, 'VAR', None) is False
    monkeypatch.delenv('TEST_VARIABLE_NOT_EXIST', raising=False)
    assert env_bool(None, 'TEST_VARIABLE_NOT_EXIST', True) is True
    monkeypatch.setenv('TEST_VARIABLE_EXIST', 'bar')
    assert env_bool(None, 'TEST_VARIABLE_EXIST', True) is False


def test_use_highlight_manually_set(monkeypatch):
    monkeypatch.delenv('TEST_DONT_USE_HIGHLIGHT', raising=False)
    assert use_highlight(highlight=True) is True
    assert use_highlight(highlight=False) is False

    monkeypatch.setenv('PY_DEVTOOLS_HIGHLIGHT', 'True')
    assert use_highlight() is True

    monkeypatch.setenv('PY_DEVTOOLS_HIGHLIGHT', 'False')
    assert use_highlight() is False


@pytest.mark.skipif(sys.platform == 'win32', reason='windows os')
def test_use_highlight_auto_not_win(monkeypatch):
    monkeypatch.delenv('TEST_DONT_USE_HIGHLIGHT', raising=False)
    monkeypatch.setattr(devtools.utils, 'isatty', lambda _=None: True)
    assert use_highlight() is True


@pytest.mark.skipif(sys.platform != 'win32', reason='not windows os')
def test_use_highlight_auto_win(monkeypatch):
    monkeypatch.delenv('TEST_DONT_USE_HIGHLIGHT', raising=False)
    monkeypatch.setattr(devtools.utils, 'isatty', lambda _=None: True)

    assert use_highlight() is True
