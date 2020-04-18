...

class lazy_debug:

    @property
    def __call__(self):
        from devtools import debug
        return debug

    def __getattr__(self, key):
        from devtools import debug
        return getattr(debug, key)

__builtins__['debug'] = lazy_debug()
