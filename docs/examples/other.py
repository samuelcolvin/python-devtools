import random

from devtools import debug

# debug.format() behaves the same as debug() except it
# returns an object to inspect or print
r = debug.format(x=123, y=321)
print(r)
print(repr(r))

values = list(range(int(1e5)))
# timer can be used as a context manager or directly
with debug.timer('shuffle values'):
    random.shuffle(values)

t2 = debug.timer('sort values').start()
sorted(values)
t2.capture()

# if used repeatedly a summary is available
t3 = debug.timer()
for i in [1e4, 1e6, 1e7]:
    with t3('sum {}'.format(i), verbose=False):
        sum(range(int(i)))

t3.summary(verbose=True)

# debug.breakpoint()
# would drop to a prompt:
# > /python-devtools/docs/examples/more_debug.py(28)<module>()->None
# -> debug.breakpoint()
# (Pdb)
