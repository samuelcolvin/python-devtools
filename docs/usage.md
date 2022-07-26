## Debug

Somehow in the 27 years (and counting) of active development of python, no one thought to add a simple
and readable way to print stuff during development. (If you know why this is, I'd love to hear).

**The wait is over:**

```py
{!examples/example.py!}
```

{{ example_html(examples/example.py) }}

`debug` is like `print` after a good night's sleep and lots of coffee:

* each output is prefixed with the file, line number and function where `debug` was called
* the variable name or expression being printed is shown
* each argument is printed "pretty" on a new line, see [prettier print](#prettier-print)
* if `pygments` is installed the output is highlighted

A more complex example of `debug` shows more of what it can do.

```py
{!examples/complex.py!}
```

{{ example_html(examples/complex.py) }}

### Returning the arguments

`debug` will return the arguments passed to it meaning you can insert `debug(...)` into code.

The returned arguments work as follows:

* if one non-keyword argument is passed to `debug()`, it is returned as-is
* if multiple arguments are passed to `debug()`, they are returned as a tuple
* if keyword arguments are passed to `debug()`, the `kwargs` dictionary is added to the returned tuple

```py
{!examples/return_args.py!}
```

{{ example_html(examples/return_args.py) }}

## Other debug tools

The debug namespace includes a number of other useful functions:

* `debug.format()` same as calling `debug()` but returns a `DebugOutput` rather than printing the output
* `debug.timer()` returns an instance of *devtool's* `Timer` class suitable for timing code execution
* `debug.breakpoint()` introduces a breakpoint using `pdb`

```py
{!examples/other.py!}
```

{{ example_html(examples/other.py) }}

### Prettier print

Python comes with [pretty print](https://docs.python.org/3/library/pprint.html), problem is quite often
it's not that pretty, it also doesn't cope well with non standard python objects (think numpy arrays or
django querysets) which have their own pretty print functionality.

To get round this *devtools* comes with prettier print, my take on pretty printing. You can see it in use above
in `debug()`, but it can also be used directly:

```py
{!examples/prettier.py!}
```

{{ example_html(examples/prettier.py) }}

For more details on prettier printing, see
[`prettier.py`](https://github.com/samuelcolvin/python-devtools/blob/master/devtools/prettier.py).

## ANSI terminal colours

```py
{!examples/ansi_colours.py!}
```

For more details on ansi colours, see
[ansi.py](https://github.com/samuelcolvin/python-devtools/blob/master/devtools/ansi.py).

## Usage without import

We all know the annoyance of running code only to discover a missing import, this can be particularly
frustrating when the function you're using isn't used except during development.

You can setup your environment to make `debug` available at all times by editing `sitecustomize.py`,
with ubuntu and python3.8 this file can be found at `/usr/lib/python3.8/sitecustomize.py` but you might
need to look elsewhere depending on your OS/python version.

Add the following to `sitecustomize.py`

```py
{!examples/sitecustomize.py!}
```

The `ImportError` exception is important since you'll want python to run fine even if *devtools* isn't installed.

This approach has another advantage: if you forget to remove `debug(...)` calls from your code, CI
(which won't have devtools installed) should fail both on execution and linting, meaning you don't end up with
extraneous debug calls in production code.
