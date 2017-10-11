from devtools import debug

v1 = {
    'bar': ['apple', 'banana', 'carrot', 'grapefruit'],
    'foo': {1: 'nested', 2: 'dict'},
}

debug(v1, sum(range(5)))
