from time import time

__all__ = ('Timer',)


class TimerResult:
    def __init__(self, name=None, verbose=True):
        self._name = name
        self.verbose = verbose
        self.finish = None
        self.start = time()

    def capture(self):
        self.finish = time()

    def elapsed(self):
        if self.finish:
            return self.finish - self.start
        else:
            return -1

    def str(self, dp=3):
        if self._name:
            return '{}: {:0.{dp}f}s elapsed'.format(self._name, self.elapsed(), dp=dp)
        else:
            return '{:0.{dp}f}s elapsed'.format(self.elapsed(), dp=dp)

    def __str__(self):
        return self.str()


_SUMMARY_TEMPLATE = '{count} times: mean={mean:0.{dp}f}s stdev={stddev:0.{dp}f}s min={min:0.{dp}f}s max={max:0.{dp}f}s'


class Timer:
    def __init__(self, name=None, verbose=True, file=None, dp=3):
        self.file = file
        self.dp = dp
        self._name = name
        self._verbose = verbose
        self.results = []

    def __call__(self, name=None, verbose=None):
        if name:
            self._name = name
        if verbose is not None:
            self._verbose = verbose
        return self

    def start(self, name=None, verbose=None):
        self.results.append(TimerResult(name or self._name, self._verbose if verbose is None else verbose))
        return self

    def capture(self, verbose=None):
        r = self.results[-1]
        r.capture()
        print_ = r.verbose if verbose is None else verbose
        if print_:
            print(r.str(self.dp), file=self.file, flush=True)
        return r

    def summary(self, verbose=False):
        times = set()
        for r in self.results:
            if not r.finish:
                r.capture()
            if verbose:
                print('    {}'.format(r.str(self.dp)), file=self.file)
            times.add(r.elapsed())

        if times:
            from statistics import mean, stdev

            print(
                _SUMMARY_TEMPLATE.format(
                    count=len(times),
                    mean=mean(times),
                    stddev=stdev(times) if len(times) > 1 else 0,
                    min=min(times),
                    max=max(times),
                    dp=self.dp,
                ),
                file=self.file,
                flush=True,
            )
        else:
            raise RuntimeError('timer not started')
        return times

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.capture()
