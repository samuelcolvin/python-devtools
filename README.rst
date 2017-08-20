python devtools
===============

|BuildStatus| |Coverage| |pypi|

Dev tools for python. **WIP**

Install
-------

Just::

    pip install python-devtools

Usage
-----

.. code:: python

   from devtools import debug

   whatever = [1, 2, 3]
   debug(whatever)

Outputs::

   test.py:4 <module>: whatever = [1, 2, 3] (list)

Usage without Import
--------------------

modify ``/usr/lib/python3.6/sitecustomize.py`` making ``debug`` available in any python 3.6 code

.. code:: python

   from devtools import debug
   __builtins__['debug'] = debug


.. |BuildStatus| image:: https://travis-ci.org/samuelcolvin/python-devtools.svg?branch=master
   :target: https://travis-ci.org/samuelcolvin/python-devtools
.. |Coverage| image:: https://codecov.io/gh/samuelcolvin/python-devtools/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/samuelcolvin/python-devtools
.. |pypi| image:: https://img.shields.io/pypi/v/python-devtools.svg
   :target: https://pypi.python.org/pypi/python-devtools
