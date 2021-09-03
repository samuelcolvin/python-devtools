## v0.7.0 (2021-09-03)

* switch to [`executing`](https://pypi.org/project/executing/) and [`asttokens`](https://pypi.org/project/asttokens/) 
  for finding and printing debug arguments, #82, thanks @alexmojaki
* correct changelog links, #76, thanks @Cielquan
* return `debug()` arguments, #87
* display more generators like `map` and `filter`, #88
* display `Counter` and similar dict-like objects properly, #88
* display `dataclasses` properly, #88
* uprev test dependencies, #81, #83, #90

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
