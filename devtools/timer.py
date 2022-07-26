from time import time

__all__ = ('Timer',)

MYPY = False
if MYPY:
    from typing import Any, List, Optional, Set

# required for type hinting because I (stupidly) added methods called `str`
StrType = str


class TimerResult:
    def __init__(self, name: 'Optional[str]' = None, verbose: bool = True) -> None:
        self._name = name
        self.verbose = verbose
        self.finish: 'Optional[float]' = None
        self.start = time()

    def capture(self) -> None:
        self.finish = time()

    def elapsed(self) -> float:
        if self.finish:
            return self.finish - self.start
        else:
            return -1

    def str(self, dp: int = 3) -> StrType:
        if self._name:
            return f'{self._name}: {self.elapsed():0.{dp}f}s elapsed'
        else:
            return f'{self.elapsed():0.{dp}f}s elapsed'

    def __str__(self) -> StrType:
        return self.str()


_SUMMARY_TEMPLATE = '{count} times: mean={mean:0.{dp}f}s stdev={stddev:0.{dp}f}s min={min:0.{dp}f}s max={max:0.{dp}f}s'


class Timer:
    def __init__(self, name: 'Optional[str]' = None, verbose: bool = True, file: 'Any' = None, dp: int = 3) -> None:
        self.file = file
        self.dp = dp
        self._name = name
        self._verbose = verbose
        self.results: 'List[TimerResult]' = []

    def __call__(self, name: 'Optional[str]' = None, verbose: 'Optional[bool]' = None) -> 'Timer':
        if name:
            self._name = name
        if verbose is not None:
            self._verbose = verbose
        return self

    def start(self, name: 'Optional[str]' = None, verbose: 'Optional[bool]' = None) -> 'Timer':
        self.results.append(TimerResult(name or self._name, self._verbose if verbose is None else verbose))
        return self

    def capture(self, verbose: 'Optional[bool]' = None) -> 'TimerResult':
        r = self.results[-1]
        r.capture()
        print_ = r.verbose if verbose is None else verbose
        if print_:
            print(r.str(self.dp), file=self.file, flush=True)
        return r

    def summary(self, verbose: bool = False) -> 'Set[float]':
        times = set()
        for r in self.results:
            if not r.finish:
                r.capture()
            if verbose:
                print(f'    {r.str(self.dp)}', file=self.file)
            times.add(r.elapsed())

        if times:
            from statistics import mean, stdev

            print(
                f'{len(times)} times: '
                f'mean={mean(times):0.{self.dp}f}s '
                f'stdev={stdev(times) if len(times) > 1 else 0:0.{self.dp}f}s '
                f'min={min(times):0.{self.dp}f}s '
                f'max={max(times):0.{self.dp}f}s',
                file=self.file,
                flush=True,
            )
        else:
            raise RuntimeError('timer not started')
        return times

    def __enter__(self) -> 'Timer':
        self.start()
        return self

    def __exit__(self, *args: 'Any') -> None:
        self.capture()
