import numpy as np

foo = {
    'foo': np.array(range(20)),
    'bar': {'apple', 'banana', 'carrot', 'grapefruit'},
    'spam': [{'a': i, 'b': {j for j in range(1 + i * 2)}} for i in range(3)],
    'gen': (i for i in ['i', 'am', 'a', 'generator']),
}
bar = {1: 2, 11: 12}

debug(foo)

# kwargs can be used as keys for what you are printing
debug(
    long_string='long strings get wrapped ' * 10,
    new_line_sring='wraps also on newline\n' * 3,
)

# debug can also show the output of expressions
debug(
    len(foo),
    bar[1],
    foo == bar
)
