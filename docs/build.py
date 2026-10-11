"""
Generate the files the docs include via `pymdownx.snippets` before zensical builds the site.

Zensical has no plugin hooks, so anything that needs Python (running the examples to capture their coloured output,
reading the package version) happens here, writing files which the markdown then includes.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

from ansi2html import Ansi2HTMLConverter

THIS_DIR = Path(__file__).parent
PROJECT_ROOT = THIS_DIR.parent

logger = logging.getLogger('docs.build')


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    build_version()
    build_examples()


def build_version() -> None:
    from devtools import __version__

    write_if_changed(THIS_DIR / '.version.md', f'Documentation for version: **v{__version__}**\n')


def build_examples() -> None:
    env = {**os.environ, 'PY_DEVTOOLS_HIGHLIGHT': 'true', 'PY_DEVTOOLS_WIDTH': '80'}
    conv = Ansi2HTMLConverter()
    for example in sorted((THIS_DIR / 'examples').glob('*.py')):
        logger.info('running %s to generate HTML...', example.relative_to(PROJECT_ROOT))
        p = subprocess.run((sys.executable, str(example)), stdout=subprocess.PIPE, check=True, env=env, cwd=THIS_DIR)
        html = conv.convert(p.stdout.decode(), full=False).strip('\r\n')
        write_if_changed(example.with_suffix('.html'), f'<pre class="ansi2html-content">\n{html}\n</pre>\n')


def write_if_changed(path: Path, content: str) -> None:
    """Avoid touching files that haven't changed so `zensical serve` doesn't rebuild needlessly."""
    if not path.exists() or path.read_text() != content:
        path.write_text(content)


if __name__ == '__main__':
    main()
