import ast
import inspect
import os
import pdb
import re
from pathlib import Path
from textwrap import dedent, indent
from typing import Generator, List, Optional, Tuple

from .ansi import isatty, sformat
from .prettier import PrettyFormat, env_true
from .timer import Timer

__all__ = 'Debug', 'debug'
CWD = Path('.').resolve()


pformat = PrettyFormat(
    indent_step=int(os.getenv('PY_DEVTOOLS_INDENT', 4)),
    simple_cutoff=int(os.getenv('PY_DEVTOOLS_SIMPLE_CUTOFF', 10)),
    width=int(os.getenv('PY_DEVTOOLS_WIDTH', 120)),
    yield_from_generators=env_true('PY_DEVTOOLS_YIELD_FROM_GEN', True),
)


class DebugArgument:
    __slots__ = 'value', 'name', 'extra'

    def __init__(self, value, *, name=None, **extra):
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

    def str(self, highlight=False) -> str:
        s = ''
        if self.name:
            s = sformat(self.name, sformat.blue, apply=highlight) + ': '

        suffix = sformat(
            ' ({.value.__class__.__name__}){}'.format(self, ''.join(' {}={}'.format(k, v) for k, v in self.extra)),
            sformat.dim,
            apply=highlight,
        )
        try:
            s += pformat(self.value, indent=4, highlight=highlight)
        except Exception as exc:
            s += '{!r}{}\n    {}'.format(
                self.value,
                suffix,
                sformat('!!! error pretty printing value: {!r}'.format(exc), sformat.yellow, apply=highlight),
            )
        else:
            s += suffix
        return s

    def __str__(self) -> str:
        return self.str()


class DebugOutput:
    """
    Represents the output of a debug command.
    """

    arg_class = DebugArgument
    __slots__ = 'filename', 'lineno', 'frame', 'arguments', 'warning'

    def __init__(self, *, filename: str, lineno: int, frame: str, arguments: List[DebugArgument], warning=None):
        self.filename = filename
        self.lineno = lineno
        self.frame = frame
        self.arguments = arguments
        self.warning = warning

    def str(self, highlight=False) -> str:
        if highlight:
            prefix = '{}:{} {}'.format(
                sformat(self.filename, sformat.magenta),
                sformat(self.lineno, sformat.green),
                sformat(self.frame, sformat.green, sformat.italic),
            )
            if self.warning:
                prefix += sformat(' ({})'.format(self.warning), sformat.dim)
        else:
            prefix = '{0.filename}:{0.lineno} {0.frame}'.format(self)
            if self.warning:
                prefix += ' ({})'.format(self.warning)
        return prefix + '\n    ' + '\n    '.join(a.str(highlight) for a in self.arguments)

    def __str__(self) -> str:
        return self.str()

    def __repr__(self) -> str:
        arguments = ' '.join(str(a) for a in self.arguments)
        return '<DebugOutput {s.filename}:{s.lineno} {s.frame} arguments: {a}>'.format(s=self, a=arguments)


class Debug:
    output_class = DebugOutput
    complex_nodes = (
        ast.Call,
        ast.Attribute,
        ast.Subscript,
        ast.IfExp,
        ast.BoolOp,
        ast.BinOp,
        ast.Compare,
        ast.DictComp,
        ast.ListComp,
        ast.SetComp,
        ast.GeneratorExp,
    )

    def __init__(
        self, *, warnings: Optional[bool] = None, highlight: Optional[bool] = None, frame_context_length: int = 50
    ):
        self._show_warnings = self._env_bool(warnings, 'PY_DEVTOOLS_WARNINGS', True)
        self._highlight = self._env_bool(highlight, 'PY_DEVTOOLS_HIGHLIGHT', None)
        # 50 lines should be enough to make sure we always get the entire function definition
        self._frame_context_length = frame_context_length

    @classmethod
    def _env_bool(cls, value, env_name, env_default):
        if value is None:
            return env_true(env_name, env_default)
        else:
            return value

    def __call__(self, *args, file_=None, flush_=True, **kwargs) -> None:
        d_out = self._process(args, kwargs, r'debug *\(')
        highlight = isatty(file_) if self._highlight is None else self._highlight
        s = d_out.str(highlight)
        print(s, file=file_, flush=flush_)

    def format(self, *args, **kwargs) -> DebugOutput:
        return self._process(args, kwargs, r'debug.format *\(')

    def breakpoint(self):
        pdb.Pdb(skip=['devtools.*']).set_trace()

    def timer(self, name=None, *, verbose=True, file=None, dp=3) -> Timer:
        return Timer(name=name, verbose=verbose, file=file, dp=dp)

    def _process(self, args, kwargs, func_regex) -> DebugOutput:
        curframe = inspect.currentframe()
        try:
            frames = inspect.getouterframes(curframe, context=self._frame_context_length)
        except IndexError:
            # NOTICE: we should really catch all conceivable errors here, if you find one please report.
            # IndexError happens in odd situations such as code called from within jinja templates
            return self.output_class(
                filename='<unknown>',
                lineno=0,
                frame='',
                arguments=list(self._args_inspection_failed(args, kwargs)),
                warning=self._show_warnings and 'error parsing code, IndexError',
            )
        # BEWARE: this must be called by a method which in turn is called "directly" for the frame to be correct
        call_frame = frames[2]

        filename = call_frame.filename
        if filename.startswith('/'):
            # make the path relative
            try:
                filename = str(Path(filename).relative_to(CWD))
            except ValueError:
                # happens if filename path is not within CWD
                pass

        if call_frame.code_context:
            func_ast, code_lines, lineno, warning = self._parse_code(call_frame, func_regex, filename)
            if func_ast:
                arguments = list(self._process_args(func_ast, code_lines, args, kwargs))
            else:
                # parsing failed
                arguments = list(self._args_inspection_failed(args, kwargs))
        else:
            lineno = call_frame.lineno
            warning = 'no code context for debug call, code inspection impossible'
            arguments = list(self._args_inspection_failed(args, kwargs))

        return self.output_class(
            filename=filename,
            lineno=lineno,
            frame=call_frame.function,
            arguments=arguments,
            warning=self._show_warnings and warning,
        )

    def _args_inspection_failed(self, args, kwargs):
        for arg in args:
            yield self.output_class.arg_class(arg)
        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name)

    def _process_args(self, func_ast, code_lines, args, kwargs) -> Generator[DebugArgument, None, None]:  # noqa: C901
        arg_offsets = list(self._get_offsets(func_ast))
        for i, arg in enumerate(args):
            try:
                ast_node = func_ast.args[i]
            except IndexError:  # pragma: no cover
                # happens when code has been commented out and there are fewer func_ast args than real args
                yield self.output_class.arg_class(arg)
                continue

            if isinstance(ast_node, ast.Name):
                yield self.output_class.arg_class(arg, name=ast_node.id)
            elif isinstance(ast_node, self.complex_nodes):
                # TODO replace this hack with astor when it get's round to a new release
                start_line, start_col = arg_offsets[i]

                if i + 1 < len(arg_offsets):
                    end_line, end_col = arg_offsets[i + 1]
                else:
                    end_line, end_col = len(code_lines) - 1, None

                name_lines = []
                for l_ in range(start_line, end_line + 1):
                    start_ = start_col if l_ == start_line else 0
                    end_ = end_col if l_ == end_line else None
                    name_lines.append(code_lines[l_][start_:end_].strip(' '))
                yield self.output_class.arg_class(arg, name=' '.join(name_lines).strip(' ,'))
            else:
                yield self.output_class.arg_class(arg)

        kw_arg_names = {}
        for kw in func_ast.keywords:
            if isinstance(kw.value, ast.Name):
                kw_arg_names[kw.arg] = kw.value.id
        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name, variable=kw_arg_names.get(name))

    def _parse_code(
        self, call_frame, func_regex, filename
    ) -> Tuple[Optional[ast.AST], Optional[List[str]], int, Optional[str]]:
        call_lines = []
        for line in range(call_frame.index, -1, -1):
            try:
                new_line = call_frame.code_context[line]
            except IndexError:  # pragma: no cover
                return None, None, line, 'error parsing code. line not found'
            call_lines.append(new_line)
            if re.search(func_regex, new_line):
                break
        call_lines.reverse()
        lineno = call_frame.lineno - len(call_lines) + 1

        code = dedent(''.join(call_lines))
        func_ast = None
        tail_index = call_frame.index
        try:
            func_ast = self._wrap_parse(code, filename)
        except (SyntaxError, AttributeError) as e1:
            # if the trailing bracket(s) of the function is/are on a new line eg.
            # debug(
            #     foo, bar,
            # )
            # inspect ignores it when setting index and we have to add it back
            for extra in range(2, 6):
                extra_lines = call_frame.code_context[tail_index + 1 : tail_index + extra]
                code = dedent(''.join(call_lines + extra_lines))
                try:
                    func_ast = self._wrap_parse(code, filename)
                except (SyntaxError, AttributeError):
                    pass
                else:
                    break

            if not func_ast:
                return None, None, lineno, 'error parsing code, {0.__class__.__name__}: {0}'.format(e1)

        if not isinstance(func_ast, ast.Call):
            return None, None, lineno, 'error parsing code, found {} not Call'.format(func_ast.__class__)

        code_lines = [line for line in code.split('\n') if line]
        # this removes the trailing bracket from the lines of code meaning it doesn't appear in the
        # representation of the last argument
        code_lines[-1] = code_lines[-1][:-1]
        return func_ast, code_lines, lineno, None

    @staticmethod
    def _wrap_parse(code, filename):
        """
        async wrapper is required to avoid await calls raising a SyntaxError
        """
        code = 'async def wrapper():\n' + indent(code, ' ')
        return ast.parse(code, filename=filename).body[0].body[0].value

    @staticmethod
    def _get_offsets(func_ast):
        for arg in func_ast.args:
            start_line, start_col = arg.lineno - 2, arg.col_offset - 1

            # horrible hack for http://bugs.python.org/issue31241
            if isinstance(arg, (ast.ListComp, ast.GeneratorExp)):
                start_col -= 1
            yield start_line, start_col
        for kw in func_ast.keywords:
            yield kw.value.lineno - 2, kw.value.col_offset - 2 - (len(kw.arg) if kw.arg else 0)


debug = Debug()
