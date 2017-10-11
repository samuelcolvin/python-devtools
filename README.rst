python devtools
===============

|BuildStatus| |Coverage| |pypi|

Dev tools for python.

The debug print command python never had (and other things).

For more information, see `documentation <https://python-devtools.helpmanual.io/>`_

Install
-------

Just::

    pip install devtools[pygments]

(``pygments`` is not required but if it's available output will be highlighted and easier to read.)

Usage
-----

.. code:: python

   from devtools import debug

   whatever = [1, 2, 3]
   debug(whatever)

Outputs::

   test.py:4 <module>:
     whatever: [1, 2, 3] (list)


That's only the tip of the iceberg, for example:

.. code:: python

   import numpy as np

   data = {
       'foo': np.array(range(20)),
       'bar': {'apple', 'banana', 'carrot', 'grapefruit'},
       'spam': [{'a': i, 'b': (i for i in range(3))} for i in range(3)],
       'sentence': 'this is just a boring sentence.\n' * 4
   }

   debug(data)

outputs:

.. image:: https://raw.githubusercontent.com/samuelcolvin/python-devtools/master/demo.py.png
    :align: center

Usage without Import
--------------------

modify ``/usr/lib/python3.6/sitecustomize.py`` making ``debug`` available in any python 3.6 code

.. code:: python

   # add devtools debug to builtins
   try:
       from devtools import debug
   except ImportError:
       pass
   else:
       __builtins__['debug'] = debug

.. |BuildStatus| image:: https://travis-ci.org/samuelcolvin/python-devtools.svg?branch=master
   :target: https://travis-ci.org/samuelcolvin/python-devtools
.. |Coverage| image:: https://codecov.io/gh/samuelcolvin/python-devtools/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/samuelcolvin/python-devtools
.. |pypi| image:: https://img.shields.io/pypi/v/devtools.svg
   :target: https://pypi.org/project/devtools
