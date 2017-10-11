from devtools import PrettyFormat, pprint, pformat

v = {
    'foo': {'whatever': [3, 2, 1]},
    'sentence': 'hello\nworld',
    'generator': (i * 2 for i in [1, 2, 3]),
}

# pretty print of v
pprint(v)

# as above without colours, the generator will also be empty as it's already been evaluated
s = pformat(v, highlight=False)
print(s)

pp = PrettyFormat(
     indent_step=2,  # default: 4
     indent_char='_',  # default: space
     repr_strings=True,  # default: False
     simple_cutoff=2,  # default: 10 (if repr is below this length it'll be shown on one line)
     width=80,  # default: 120
     yield_from_generators=False  # default: True (whether to evaluate generators)
)

print(pp(v, highlight=True))
