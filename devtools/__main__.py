import builtins
import sys
from pathlib import Path

from .version import VERSION

# language=python
install_code = """
# add devtools `debug` function to builtins
# we don't want to import devtools until it's required since it breaks pytest, hence this proxy
class DebugProxy:
    def __init__(self):
        self._debug = None

    def _import_debug(self):
        if self._debug is None:
            from devtools import debug
            self._debug = debug

    def __call__(self, *args, **kwargs):
        self._import_debug()
        kwargs['frame_depth_'] = 3
        return self._debug(*args, **kwargs)

    def format(self, *args, **kwargs):
        self._import_debug()
        kwargs['frame_depth_'] = 3
        return self._debug.format(*args, **kwargs)

    def __getattr__(self, item):
        self._import_debug()
        return getattr(self._debug, item)

import builtins
setattr(builtins, 'debug', DebugProxy())
"""


def print_code() -> int:
    print(install_code)
    return 0


def install() -> int:
    try:
        import sitecustomize  # type: ignore
    except ImportError:
        paths = [Path(p) for p in sys.path]
        try:
            path = next(p for p in paths if p.is_dir() and p.name == 'site-packages')
        except StopIteration:
            # what else makes sense to try?
            print(f'unable to file a suitable path to save `sitecustomize.py` to from sys.path: {paths}')
            return 1
        else:
            install_path = path / 'sitecustomize.py'
    else:
        install_path = Path(sitecustomize.__file__)

    if hasattr(builtins, 'debug'):
        print(f'Looks like devtools is already installed, probably in `{install_path}`.')
        return 0

    print(f'Found path `{install_path}` to install devtools into `builtins`')
    print('To install devtools, run the following command:\n')
    print(f'    python -m devtools print-code >> {install_path}\n')
    if not install_path.is_relative_to(Path.home()):
        print('or maybe\n')
        print(f'    python -m devtools print-code | sudo tee -a {install_path} > /dev/null\n')
        print('Note: "sudo" might be required because the path is in your home directory.')

    return 0


if __name__ == '__main__':
    if 'install' in sys.argv:
        sys.exit(install())
    elif 'print-code' in sys.argv:
        sys.exit(print_code())
    else:
        print(f'python-devtools v{VERSION}, CLI usage: `python -m devtools install|print-code`')
        sys.exit(1)
