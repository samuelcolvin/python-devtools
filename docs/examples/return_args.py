from devtools import debug

assert debug('foo') == 'foo'
assert debug('foo', 'bar') == ('foo', 'bar')
assert debug('foo', 'bar', spam=123) == ('foo', 'bar', {'spam': 123})
assert debug(spam=123) == ({'spam': 123},)
