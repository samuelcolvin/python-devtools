import numpy as np

foo = {
    'foo': np.array(range(20)),
    'bar': {'apple', 'banana', 'carrot', 'grapefruit'},
    'spam': [{'a': i, 'b': {j for j in range(1 + i * 2)}} for i in range(3)],
    'sentence': 'this is just a boring sentence.\n' * 4
}
bar = {1: 2}

debug(foo, bar[1], spam='hello')
