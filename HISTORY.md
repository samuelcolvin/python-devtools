## v0.12.1 (2023-08-17)

fix docs release

## v0.12.0 (2023-08-17)

* build docs on CI by @samuelcolvin in #127
* Update usage to reflect the recent addition of the pytest plugin by @tomhamiltonstubber in #128
* support dataclasses with slots by @samuelcolvin in #136
* Make `Pygments` required #137

## v0.11.0 (2023-04-05)

* added support for sqlalchemy2 by @the-vty in #120
* switch to ruff by @samuelcolvin in #124
* support displaying ast types by @samuelcolvin in #125
* Insert assert by @samuelcolvin in #126

## v0.10.0 (2022-11-28)

* Use secure builtins standard module, instead of the `__builtins__` by @0xsirsaif in #109
* upgrade executing to fix 3.10 by @samuelcolvin in #110
* Fix windows build by @samuelcolvin in #111
* Allow executing dependency to be >1.0.0 by @staticf0x in #115
* more precise timer summary by @banteg in #113
* Python 3.11 by @samuelcolvin in #118

## v0.9.0 (2022-07-26)

* fix format of nested dataclasses, #99 thanks @aliereno
* Moving to `pyproject.toml`, complete type hints and test with mypy, #107
* add `install` command to add `debug` to `__builtins__`, #108

## v0.8.0 (2021-09-29)

* test with python 3.10 #91
* display `SQLAlchemy` objects nicely #94
* fix tests on windows #93
* show function `qualname` #95
* cache pygments loading (significant speedup) #96

## v0.7.0 (2021-09-03)

* switch to [`executing`](https://pypi.org/project/executing/) and [`asttokens`](https://pypi.org/project/asttokens/)
  for finding and printing debug arguments, #82, thanks @alexmojaki
* correct changelog links, #76, thanks @Cielquan
* return `debug()` arguments, #87
* display more generators like `map` and `filter`, #88
* display `Counter` and similar dict-like objects properly, #88
* display `dataclasses` properly, #88
* uprev test dependencies, #81, #83, #90

## v0.6.1 (2020-10-22)

compatibility with python 3.8.6

## v0.6.0 (2020-07-29)

* improve `__pretty__` to work better with pydantic classes, #52
* improve the way statement ranges are calculated, #58
* drastically improve import time, #50
* pretty printing for non-standard dicts, #60
* better statement finding for multi-line statements, #61
* colors in windows, #57
* fix `debug(type(dict(...)))`, #62

## v0.5.1 (2019-10-09)

* fix python tag in `setup.cfg`, #46

## v0.5.0 (2019-01-03)

* support `MultiDict`, #34
* support `__pretty__` method, #36

## v0.4.0 (2018-12-29)

* remove use of `warnings`, include in output, #30
* fix rendering errors #31
* better str and bytes wrapping #32
* add `len` everywhere possible, part of #16

## v0.3.0 (2017-10-11)

* allow `async/await` arguments
* fix subscript
* fix weird named tuples eg. `mock > call_args`
* add `timer`

## v0.2.0 (2017-09-14)

* improve output
* numerous bug fixes
