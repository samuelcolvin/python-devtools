import importlib
import sys

__all__ = ('isatty', 'LazyIsInstance')


def isatty(stream=None):
    stream = stream or sys.stdout
    try:
        return stream.isatty()
    except Exception:
        return False


class LazyIsInstanceMeta(type):
    _package_path: str
    _cls_name: str
    _t = None

    def __instancecheck__(self, instance):
        if self._t is None:

            try:
                m = importlib.import_module(self._package_path)
            except ImportError:
                self._t = False
            else:
                self._t = getattr(m, self._cls_name)

        return self._t and isinstance(instance, self._t)

    def __getitem__(self, item):
        package_path, cls_name = item
        return type(cls_name, (self,), {'_package_path': package_path, '_cls_name': cls_name, '_t': None})


class LazyIsInstance(metaclass=LazyIsInstanceMeta):
    pass
