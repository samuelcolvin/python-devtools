import os

import pytest

pytest_plugins = ['pytester']


def pytest_sessionstart(session: pytest.Session) -> None:
    os.environ.pop('PY_DEVTOOLS_HIGHLIGHT', None)
