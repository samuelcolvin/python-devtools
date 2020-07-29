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
