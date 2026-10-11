#!/usr/bin/env python3
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from ansi2html import Ansi2HTMLConverter
from mkdocs.config import Config
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page

THIS_DIR = Path(__file__).parent
PROJECT_ROOT = THIS_DIR / '..'

logger = logging.getLogger('mkdocs.test_examples')

# see mkdocs.yml for how these methods ar used
__all__ = 'on_files', 'on_page_markdown', 'on_pre_build'


def on_pre_build(config: Config) -> None:
    build_history()


def on_page_markdown(markdown: str, page: Page, config: Config, files: Files) -> str:
    markdown = set_version(markdown, page)
    return gen_example_html(markdown)


def on_files(files: Files, config: Config) -> Files:
    return remove_files(files)


def build_history() -> None:
    history = (PROJECT_ROOT / 'HISTORY.md').read_text()
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/samuelcolvin/python-devtools/issues/\1)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.IGNORECASE)
    history = re.sub('@@', '@', history)
    output_file = THIS_DIR / '.history.md'
    if not output_file.exists() or history != output_file.read_text():
        (THIS_DIR / '.history.md').write_text(history)


def gen_example_html(markdown: str) -> str:
    return re.sub(r'{{ *example_html\((.*?)\) *}}', gen_examples_html, markdown)


def gen_examples_html(m: re.Match[str]) -> str:
    sys.path.append(str(THIS_DIR.resolve()))

    os.environ.update(PY_DEVTOOLS_HIGHLIGHT='true', PY_DEVTOOLS_WIDTH='80')
    conv = Ansi2HTMLConverter()
    name = THIS_DIR / m.group(1)

    logger.info('running %s to generate HTML...', name)
    p = subprocess.run((sys.executable, str(name)), stdout=subprocess.PIPE, check=True)
    html = conv.convert(p.stdout.decode(), full=False).strip('\r\n')
    html = html.replace('docs/build/../examples/', '')
    return f'<pre class="ansi2html-content">\n{html}\n</pre>\n'


def set_version(markdown: str, page: Page) -> str:
    if page.abs_url == '/':
        from devtools import __version__

        version_str = f'Documentation for version: **v{__version__}**'
        markdown = re.sub(r'{{ *version *}}', version_str, markdown)
    return markdown


def remove_files(files: Files) -> Files:
    to_remove: list[File] = []
    for file in files:
        if file.src_path.startswith('__pycache__/') or file.src_path.endswith('.py'):
            to_remove.append(file)

    logger.debug('removing files: %s', [f.src_path for f in to_remove])
    for f in to_remove:
        files.remove(f)

    return files
