from devtools import debug
import numpy as np

foo = {
    'foo': np.array(range(20)),
    'bar': [{'a': i, 'b': {j for j in range(1 + i * 2)}} for i in range(3)],
    'spam': (i for i in ['i', 'am', 'a', 'generator']),
}

debug(foo)

# kwargs can be used as keys for what you are printing
debug(
    long_string='long strings get wrapped ' * 10,
    new_line_string='wraps also on newline\n' * 3,
)

bar = {1: 2, 11: 12}
# debug can also show the output of expressions
debug(
    len(foo),
    bar[1],
    foo == bar
)
