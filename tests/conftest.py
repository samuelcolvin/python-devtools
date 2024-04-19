import os

pytest_plugins = ['pytester']


def pytest_sessionstart(session):
    os.environ.pop('PY_DEVTOOLS_HIGHLIGHT', None)
    os.environ['PY_DEVTOOLS_STYLE'] = 'vim'
