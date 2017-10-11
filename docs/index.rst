python-devtools
===============

.. toctree::
   :maxdepth: 2

|pypi| |license|

Current Version: |version|

Dev tools for python.

Install
-------

Assuming you have **python 3.5+** and pip installed, just::

    pip install devtools

If ``pygments`` is installed *devtools* will colourise output to make it even more readable. The
chances are you already have pygments installed if you're using ipython, otherwise it can be installed along
with *devtools* via ``pip install devtools[pygments]``.

debug print
-----------

Example:

.. literalinclude:: examples/1_input.py

Will output:

.. image:: examples/1_output.png

``debug`` is like ``print`` on steroids, and coffee, and some orange pills
you found down the back of a chair on the tube:

* Each output it prefixed with the file, line number and function where ``debug`` was called
* the variable name or expression being printed is shown
* each argument is printed "pretty" on a new line with
* if ``pygments`` is installed the output will be highlighted

a more complex example of ``debug`` shows more of what it can do.

.. literalinclude:: examples/2_input.py

Will output:

.. image:: examples/2_output.png



.. include:: ../HISTORY.rst


.. |pypi| image:: https://img.shields.io/pypi/v/python-devtools.svg
   :target: https://pypi.python.org/pypi/python-devtools
.. |license| image:: https://img.shields.io/pypi/l/python-devtools.svg
   :target: https://github.com/samuelcolvin/python-devtools
