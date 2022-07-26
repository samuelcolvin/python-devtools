#!/usr/bin/env python3
import logging
import os
import re
import sys
import subprocess
from pathlib import Path

import requests
from setuptools.config import pyprojecttoml
from ansi2html import Ansi2HTMLConverter

from mkdocs.config import Config
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

THIS_DIR = Path(__file__).parent
PROJECT_ROOT = THIS_DIR / '..'

logger = logging.getLogger('mkdocs.test_examples')

# see mkdocs.yml for how these methods ar used
__all__ = 'on_pre_build', 'on_page_markdown', 'on_files'


def on_pre_build(config: Config):
    build_history()


def on_page_markdown(markdown: str, page: Page, config: Config, files: Files) -> str:
    markdown = set_version(markdown, page)
    return gen_example_html(markdown)


def on_files(files: Files, config: Config) -> Files:
    return remove_files(files)


def build_history():
    output_file = THIS_DIR / '.history.md'
    if output_file.exists():
        return
    logger.info('generating history from github releases...')
    r = requests.get('https://api.github.com/repos/samuelcolvin/python-devtools/releases')
    r.raise_for_status()
    releases = r.json()

    history = []
    for release in releases:
        body = release['body'].replace('\r\n', '\n').strip(' \n') or '_(no details available)_'
        history.append(f'## {release["name"]}\n\n{body}')

    history = '\n\n'.join(history)
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/samuelcolvin/python-devtools/issues/\1)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)
    output_file.write_text(history)


def gen_example_html(markdown: str):
    return re.sub(r'{{ *example_html\((.*?)\) *}}', gen_examples_html, markdown)


def gen_examples_html(m: re.Match) -> str:
    sys.path.append(str(THIS_DIR.resolve()))

    os.environ.update(PY_DEVTOOLS_HIGHLIGHT='true', PY_DEVTOOLS_WIDTH='80')
    conv = Ansi2HTMLConverter()
    name = THIS_DIR / Path(m.group(1))

    logger.info("running %s to generate HTML...", name)
    p = subprocess.run((sys.executable, str(name)), stdout=subprocess.PIPE, check=True)
    html = conv.convert(p.stdout.decode(), full=False).strip('\r\n')
    html = html.replace('docs/build/../examples/', '')
    return f'<pre class="ansi2html-content">\n{html}\n</pre>\n'


def set_version(markdown: str, page: Page) -> str:
    if page.abs_url == '/':
        version = pyprojecttoml.load_file('pyproject.toml')['project']['version']
        version_str = f'Documentation for version: **{version}**'
        markdown = re.sub(r'{{ *version *}}', version_str, markdown)
    return markdown


def remove_files(files: Files) -> Files:
    to_remove = []
    for file in files:
        if file.src_path in {'plugins.py', 'requirements.txt'}:
            to_remove.append(file)
        elif file.src_path.startswith('__pycache__/'):
            to_remove.append(file)

    logger.debug('removing files: %s', [f.src_path for f in to_remove])
    for f in to_remove:
        files.remove(f)

    return files
