from devtools import debug

data = {
    'foo': (i for i in ['i', 'am', 'a', 'generator']),
    'bar': {'apple', 'banana', 'carrot', 'grapefruit'},
}

debug(data)
