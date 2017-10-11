#!/usr/bin/env python
import os
import subprocess
import sys
from pathlib import Path

from ansi2html import Ansi2HTMLConverter

EX_DIR = Path(__file__).parent / 'examples'
os.environ.update(
    PY_DEVTOOLS_HIGHLIGHT='true',
)
conv = Ansi2HTMLConverter()


def gen_html(name):
    p = subprocess.run((sys.executable, str(EX_DIR / '{}.py'.format(name))), stdout=subprocess.PIPE, check=True)
    html = conv.convert(p.stdout.decode(), full=False).strip('\r\n')
    html = '<pre class="ansi2html-content">\n{}\n</pre>'.format(html)
    (EX_DIR / '{}.html'.format(name)).write_text(html)


gen_html('example1')
gen_html('example2')
gen_html('prettier')
