...

try:
    from devtools import debug
except ImportError:
    pass
else:
    __builtins__['debug'] = debug
