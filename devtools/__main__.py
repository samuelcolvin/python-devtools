import builtins
import sys
from pathlib import Path

from .version import VERSION

# language=python
install_code = """
# add devtools `debug` function to builtins
import sys
# we don't install here for pytest as it breaks pytest, it is
# installed later by a pytest fixture
if not sys.argv[0].endswith('pytest'):
    import builtins
    try:
        from devtools import debug
    except ImportError:
        pass
    else:
        setattr(builtins, 'debug', debug)
"""


def print_code() -> int:
    print(install_code)
    return 0


def install() -> int:
    print('[WARNING: this command is experimental, report issues at github.com/samuelcolvin/python-devtools]\n')

    if hasattr(builtins, 'debug'):
        print('Looks like devtools is already installed.')
        return 0

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

    print(f'Found path "{install_path}" to install devtools into __builtins__')
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
        print(f'python-devtools v{VERSION}, CLI usage: python -m devtools [install|print-code]')
        sys.exit(1)
