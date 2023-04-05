import numpy as np

from devtools import PrettyFormat, pformat, pprint

v = {
    'foo': {'whatever': [3, 2, 1]},
    'sentence': 'hello\nworld',
    'generator': (i * 2 for i in [1, 2, 3]),
    'matrix': np.matrix([[1, 2, 3, 4],
                         [50, 60, 70, 80],
                         [900, 1000, 1100, 1200],
                         [13000, 14000, 15000, 16000]])
}

# pretty print of v
pprint(v)

# as above without colours, the generator will also be empty as
# it's already been evaluated
s = pformat(v, highlight=False)
print(s)

pp = PrettyFormat(
    indent_step=2,  # default: 4
    indent_char='.',  # default: space
    repr_strings=True,  # default: False
    # default: 10 (if line is below this length it'll be shown on one line)
    simple_cutoff=2,
    width=80,  # default: 120
    # default: True (whether to evaluate generators
    yield_from_generators=False,
)

print(pp(v, highlight=True))
