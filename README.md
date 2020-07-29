# python devtools

[![CI](https://github.com/samuelcolvin/python-devtools/workflows/CI/badge.svg?event=push)](https://github.com/samuelcolvin/python-devtools/actions?query=event%3Apush+branch%3Amaster+workflow%3ACI)
[![Coverage](https://codecov.io/gh/samuelcolvin/python-devtools/branch/master/graph/badge.svg)](https://codecov.io/gh/samuelcolvin/python-devtools)
[![pypi](https://img.shields.io/pypi/v/devtools.svg)](https://pypi.python.org/pypi/devtools)
[![versions](https://img.shields.io/pypi/pyversions/devtools.svg)](https://github.com/samuelcolvin/python-devtools)
[![license](https://img.shields.io/github/license/samuelcolvin/python-devtools.svg)](https://github.com/samuelcolvin/python-devtools/blob/master/LICENSE)

**Python's missing debug print command and other development tools.**

For more information, see [documentation](https://python-devtools.helpmanual.io/).

## Install

Just

```bash
pip install devtools[pygments]
```

`pygments` is not required but if it's installed, output will be highlighted and easier to read.

`devtools` has no other required dependencies except python 3.6, 3.7, or 3.8.
If you've got python 3.6+ and `pip` installed, you're good to go.

## Usage

```py
from devtools import debug

whatever = [1, 2, 3]
debug(whatever)
```

Outputs:

```py
test.py:4 <module>:
    whatever: [1, 2, 3] (list)
```


That's only the tip of the iceberg, for example:

```py
import numpy as np

data = {
    'foo': np.array(range(20)),
    'bar': {'apple', 'banana', 'carrot', 'grapefruit'},
    'spam': [{'a': i, 'b': (i for i in range(3))} for i in range(3)],
    'sentence': 'this is just a boring sentence.\n' * 4
}

debug(data)
```

outputs:

![python-devtools demo](https://raw.githubusercontent.com/samuelcolvin/python-devtools/master/demo.py.png)

## Usage without Import

modify `/usr/lib/python3.8/sitecustomize.py` making `debug` available in any python 3.8 code

```py
# add devtools debug to builtins
try:
    from devtools import debug
except ImportError:
    pass
else:
    __builtins__['debug'] = debug
```
