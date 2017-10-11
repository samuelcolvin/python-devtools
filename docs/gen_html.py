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

for f in EX_DIR.iterdir():
    if f.suffix != '.py' or f.name == 'sitecustomize.py':
        continue
    print('generating output for: {}'.format(f))
    p = subprocess.run((sys.executable, str(f)), stdout=subprocess.PIPE, check=True)
    html = conv.convert(p.stdout.decode(), full=False).strip('\r\n')
    html = '<pre class="ansi2html-content">\n{}\n</pre>'.format(html)
    (EX_DIR / '{}.html'.format(f.stem)).write_text(html)
