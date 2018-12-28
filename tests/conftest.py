import os


def pytest_sessionstart(session):
    os.environ.pop('PY_DEVTOOLS_HIGHLIGHT', None)
