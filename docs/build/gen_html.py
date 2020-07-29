import os
import subprocess
import sys
from pathlib import Path

from ansi2html import Ansi2HTMLConverter

EX_DIR = Path(__file__).parent / '..' / 'examples'


def gen_examples_html():
    os.environ.update(PY_DEVTOOLS_HIGHLIGHT='true', PY_DEVTOOLS_WIDTH='80')
    conv = Ansi2HTMLConverter()
    fast = 'FAST' in os.environ

    for f in EX_DIR.iterdir():
        if f.suffix != '.py' or f.name == 'sitecustomize.py':
            continue
        output_file = EX_DIR / f'{f.stem}.html'
        if fast and output_file.exists():
            print(f'HTML file already exists for {f}, skipping')
            continue

        print(f'generating output for: {f}')
        p = subprocess.run((sys.executable, str(f)), stdout=subprocess.PIPE, check=True)
        html = conv.convert(p.stdout.decode(), full=False).strip('\r\n')
        html = html.replace('docs/build/../examples/', '')
        output_file.write_text(f'<pre class="ansi2html-content">\n{html}\n</pre>\n')


if __name__ == '__main__':
    gen_examples_html()
