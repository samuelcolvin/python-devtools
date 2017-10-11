from devtools import debug

v1 = {
    'foo': {1: 'nested', 2: 'dict'},
    'bar': ['apple', 'banana', 'carrot', 'grapefruit'],
}

debug(v1, sum(range(5)))
