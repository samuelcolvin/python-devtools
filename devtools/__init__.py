# flake8: noqa
from .ansi import *
from .debug import *
from .prettier import *
from .timer import *
try:
    from .version import VERSION
except ImportError:
    # version is set by running .github/set_version.py to create devtools/version.py
    VERSION = '0'

__version__ = VERSION
