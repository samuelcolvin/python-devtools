from devtools import PrettyFormat, pprint, pformat

v = {
    'foo': {'whatever': [3, 2, 1]},
    'sentence': 'hello\nworld',
    'generator': (i * 2 for i in [1, 2, 3]),
}

pprint(v)
# > with colours:
"""
{
    'foo': {
        'whatever': [3, 2, 1],
    },
    'sentence': (
        'hello\n'
        'world'
    ),
    'generator': (
        2,
        4,
        6,
    ),
}
"""

s = pformat(v, highlight=False)
print(s)
# > as above without colours, the generator will also be empty as it's already been evaluated

pp = PrettyFormat(
     indent_step=2,  # default: 4
     indent_char='_',  # default: space
     repr_strings=True,  # default: False
     simple_cutoff=2,  # default: 10 (if repr is below this length it'll be shown on one line)
     width=80,  # default: 120
     yield_from_generators=False  # default: True (whether to evaluate generators)
)

print(pp(v))
# >
"""
{
__'foo': {
____'whatever': [
______'apple',
______123,
______45.67,
____],
__},
__'sentence': 'hello\nworld',
__'generator': <generator object <genexpr> at 0x7f448b7cebf8>,
}
"""
