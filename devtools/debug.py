import os
import sys

from .ansi import sformat
from .prettier import PrettyFormat
from .timer import Timer
from .utils import env_bool, env_true, is_literal, use_highlight

__all__ = 'Debug', 'debug'
MYPY = False
if MYPY:
    from types import FrameType
    from typing import Any, Generator, List, Optional, Union

pformat = PrettyFormat(
    indent_step=int(os.getenv('PY_DEVTOOLS_INDENT', 4)),
    simple_cutoff=int(os.getenv('PY_DEVTOOLS_SIMPLE_CUTOFF', 10)),
    width=int(os.getenv('PY_DEVTOOLS_WIDTH', 120)),
    yield_from_generators=env_true('PY_DEVTOOLS_YIELD_FROM_GEN', True),
)
# required for type hinting because I (stupidly) added methods called `str`
StrType = str


class DebugArgument:
    __slots__ = 'value', 'name', 'extra'

    def __init__(self, value: 'Any', *, name: 'Optional[str]' = None, **extra: 'Any') -> None:
        self.value = value
        self.name = name
        self.extra = []
        try:
            length = len(value)
        except TypeError:
            pass
        else:
            self.extra.append(('len', length))
        self.extra += [(k, v) for k, v in extra.items() if v is not None]

    def str(self, highlight: bool = False) -> StrType:
        s = ''
        if self.name and not is_literal(self.name):
            s = f'{sformat(self.name, sformat.blue, apply=highlight)}: '

        suffix = sformat(
            f" ({self.value.__class__.__name__}){''.join(f' {k}={v}' for k, v in self.extra)}",
            sformat.dim,
            apply=highlight,
        )
        try:
            s += pformat(self.value, indent=4, highlight=highlight)
        except Exception as exc:
            v = sformat(f'!!! error pretty printing value: {exc!r}', sformat.yellow, apply=highlight)
            s += f'{self.value!r}{suffix}\n    {v}'
        else:
            s += suffix
        return s

    def __str__(self) -> StrType:
        return self.str()


class DebugOutput:
    """
    Represents the output of a debug command.
    """

    arg_class = DebugArgument
    __slots__ = 'filename', 'lineno', 'frame', 'arguments', 'warning'

    def __init__(
        self,
        *,
        filename: str,
        lineno: int,
        frame: str,
        arguments: 'List[DebugArgument]',
        warning: 'Union[None, str, bool]' = None,
    ) -> None:
        self.filename = filename
        self.lineno = lineno
        self.frame = frame
        self.arguments = arguments
        self.warning = warning

    def str(self, highlight: bool = False) -> StrType:
        if highlight:
            prefix = (
                f'{sformat(self.filename, sformat.magenta)}:{sformat(self.lineno, sformat.green)} '
                f'{sformat(self.frame, sformat.green, sformat.italic)}'
            )
            if self.warning:
                prefix += sformat(f' ({self.warning})', sformat.dim)
        else:
            prefix = f'{self.filename}:{self.lineno} {self.frame}'
            if self.warning:
                prefix += f' ({self.warning})'
        return f'{prefix}\n    ' + '\n    '.join(a.str(highlight) for a in self.arguments)

    def __str__(self) -> StrType:
        return self.str()

    def __repr__(self) -> StrType:
        arguments = ' '.join(str(a) for a in self.arguments)
        return f'<DebugOutput {self.filename}:{self.lineno} {self.frame} arguments: {arguments}>'


class Debug:
    output_class = DebugOutput

    def __init__(self, *, warnings: 'Optional[bool]' = None, highlight: 'Optional[bool]' = None):
        self._show_warnings = env_bool(warnings, 'PY_DEVTOOLS_WARNINGS', True)
        self._highlight = highlight

    def __call__(self, *args: 'Any', file_: 'Any' = None, flush_: bool = True, **kwargs: 'Any') -> 'Any':
        d_out = self._process(args, kwargs)
        s = d_out.str(use_highlight(self._highlight, file_))
        print(s, file=file_, flush=flush_)
        if kwargs:
            return (*args, kwargs)
        elif len(args) == 1:
            return args[0]
        else:
            return args

    def format(self, *args: 'Any', **kwargs: 'Any') -> DebugOutput:
        return self._process(args, kwargs)

    def breakpoint(self) -> None:
        import pdb

        pdb.Pdb(skip=['devtools.*']).set_trace()

    def timer(self, name: 'Optional[str]' = None, *, verbose: bool = True, file: 'Any' = None, dp: int = 3) -> Timer:
        return Timer(name=name, verbose=verbose, file=file, dp=dp)

    def _process(self, args: 'Any', kwargs: 'Any') -> DebugOutput:
        """
        BEWARE: this must be called from a function exactly 2 levels below the top of the stack.
        """
        # HELP: any errors other than ValueError from _getframe? If so please submit an issue
        try:
            call_frame: 'FrameType' = sys._getframe(2)
        except ValueError:
            # "If [ValueError] is deeper than the call stack, ValueError is raised"
            return self.output_class(
                filename='<unknown>',
                lineno=0,
                frame='',
                arguments=list(self._args_inspection_failed(args, kwargs)),
                warning=self._show_warnings and 'error parsing code, call stack too shallow',
            )

        function = call_frame.f_code.co_name

        from pathlib import Path

        path = Path(call_frame.f_code.co_filename)
        if path.is_absolute():
            # make the path relative
            cwd = Path('.').resolve()
            try:
                path = path.relative_to(cwd)
            except ValueError:
                # happens if filename path is not within CWD
                pass

        lineno = call_frame.f_lineno
        warning = None

        import executing

        source = executing.Source.for_frame(call_frame)
        if not source.text:
            warning = 'no code context for debug call, code inspection impossible'
            arguments = list(self._args_inspection_failed(args, kwargs))
        else:
            ex = source.executing(call_frame)
            function = ex.code_qualname()
            if not ex.node:
                warning = 'executing failed to find the calling node'
                arguments = list(self._args_inspection_failed(args, kwargs))
            else:
                arguments = list(self._process_args(ex, args, kwargs))

        return self.output_class(
            filename=str(path),
            lineno=lineno,
            frame=function,
            arguments=arguments,
            warning=self._show_warnings and warning,
        )

    def _args_inspection_failed(self, args: 'Any', kwargs: 'Any') -> 'Generator[DebugArgument, None, None]':
        for arg in args:
            yield self.output_class.arg_class(arg)
        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name)

    def _process_args(self, ex: 'Any', args: 'Any', kwargs: 'Any') -> 'Generator[DebugArgument, None, None]':
        import ast

        func_ast = ex.node
        atok = ex.source.asttokens()
        for arg, ast_arg in zip(args, func_ast.args):
            if isinstance(ast_arg, ast.Name):
                yield self.output_class.arg_class(arg, name=ast_arg.id)
            else:
                name = ' '.join(map(str.strip, atok.get_text(ast_arg).splitlines()))
                yield self.output_class.arg_class(arg, name=name)

        kw_arg_names = {}
        for kw in func_ast.keywords:
            if isinstance(kw.value, ast.Name):
                kw_arg_names[kw.arg] = kw.value.id

        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name, variable=kw_arg_names.get(name))


debug = Debug()
