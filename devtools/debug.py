import ast
import inspect
import os
import re
import warnings
from pathlib import Path
from textwrap import dedent
from typing import Generator, List, Optional, Tuple

from .ansi import isatty, sformat
from .prettier import PrettyFormat

__all__ = ['Debug', 'debug']
CWD = Path('.').resolve()


def env_true(var_name, alt='FALSE'):
    return os.getenv(var_name, alt).upper() in {'1', 'TRUE'}


pformat = PrettyFormat(
    indent_step=int(os.getenv('PY_DEVTOOLS_INDENT', 4)),
    simple_cutoff=int(os.getenv('PY_DEVTOOLS_SIMPLE_CUTOFF', 10)),
    width=int(os.getenv('PY_DEVTOOLS_SIMPLE_TERM_WIDTH', 120)),
    yield_from_generators=env_true('PY_DEVTOOLS_YIELD_FROM_GEN', 'TRUE'),
)


class DebugArgument:
    __slots__ = 'value', 'name', 'extra'

    def __init__(self, value, *, name=None, **extra):
        self.value = value
        self.name = name
        self.extra = []
        if isinstance(value, (str, bytes)):
            self.extra.append(('len', len(value)))
        self.extra += [(k, v) for k, v in extra.items() if v is not None]

    def str(self, colour=False, highlight=False) -> str:
        s = ''
        if self.name:
            s = sformat(self.name, sformat.blue, apply=colour) + ': '
        s += pformat(self.value, indent=2, highlight=highlight)
        suffix = (
            ' ({0.value.__class__.__name__}) {1}'
            .format(self, ' '.join('{}={}'.format(k, v) for k, v in self.extra))
            .rstrip(' ')  # trailing space if extra is empty
        )
        s += sformat(suffix, sformat.dim, apply=colour)
        return s

    def __str__(self) -> str:
        return self.str()


class DebugOutput:
    """
    Represents the output of a debug command.
    """
    arg_class = DebugArgument
    __slots__ = 'filename', 'lineno', 'frame', 'arguments'

    def __init__(self, *, filename: str, lineno: int, frame: str, arguments: List[DebugArgument]):
        self.filename = filename
        self.lineno = lineno
        self.frame = frame
        self.arguments = arguments

    def str(self, colour=False, highlight=False) -> str:
        if colour:
            prefix = '{}:{} {}\n  '.format(
                sformat(self.filename, sformat.magenta),
                sformat(self.lineno, sformat.green),
                sformat(self.frame, sformat.green, sformat.italic)
            )
        else:
            prefix = '{0.filename}:{0.lineno} {0.frame}\n  '.format(self)
        return prefix + '\n  '.join(a.str(colour, highlight) for a in self.arguments)

    def __str__(self) -> str:
        return self.str()

    def __repr__(self) -> str:
        arguments = ' '.join(str(a) for a in self.arguments)
        return '<DebugOutput {s.filename}:{s.lineno} {s.frame} arguments: {a}>'.format(s=self, a=arguments)


class Debug:
    output_class = DebugOutput
    complex_nodes = (
        ast.Call, ast.Attribute,
        ast.IfExp, ast.BoolOp, ast.BinOp, ast.Compare,
        ast.DictComp, ast.ListComp, ast.SetComp, ast.GeneratorExp
    )

    def __init__(self, *,
                 warnings: Optional[bool]=None,
                 colour: Optional[bool]=None,
                 highlight: Optional[bool]=None,
                 frame_context_length: int=50):
        self._warnings = self._env_bool(warnings, 'PY_DEVTOOLS_WARNINGS')
        self._colour = self._env_bool(colour, 'PY_DEVTOOLS_COLOUR')
        self._highlight = self._env_bool(highlight, 'PY_DEVTOOLS_HIGHLIGHT')
        # 50 lines should be enough to make sure we always get the entire function definition
        self._frame_context_length = frame_context_length

    @classmethod
    def _env_bool(cls, value, env_name, env_default='TRUE'):
        if value is None:
            return env_true(env_name, env_default)
        else:
            return value

    def __call__(self, *args, file_=None, flush_=True, **kwargs) -> None:
        d_out = self._process(args, kwargs, r'debug *\(')
        colours_possible = isatty(file_)
        s = d_out.str(self._colour and colours_possible, self._highlight and colours_possible)
        print(s, file=file_, flush=flush_)

    def format(self, *args, **kwargs) -> DebugOutput:
        return self._process(args, kwargs, r'debug.format *\(')

    def _process(self, args, kwargs, func_regex) -> DebugOutput:
        curframe = inspect.currentframe()
        frames = inspect.getouterframes(curframe, context=self._frame_context_length)
        # BEWARE: this must be call by a method which in turn is called "directly" for the frame to be correct
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
            func_ast, code_lines, lineno = self._parse_code(call_frame, func_regex, filename)
            if func_ast:
                arguments = list(self._process_args(func_ast, code_lines, args, kwargs))
            else:
                # parsing failed
                arguments = list(self._args_inspection_failed(args, kwargs))
        else:
            lineno = call_frame.lineno
            if self._warnings:
                warnings.warn('no code context for debug call, code inspection impossible', RuntimeWarning)
            arguments = list(self._args_inspection_failed(args, kwargs))

        return self.output_class(
            filename=filename,
            lineno=lineno,
            frame=call_frame.function,
            arguments=arguments
        )

    def _args_inspection_failed(self, args, kwargs):
        for arg in args:
            yield self.output_class.arg_class(arg)
        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name)

    def _process_args(self, func_ast, code_lines, args, kwargs) -> Generator[DebugArgument, None, None]:  # noqa: C901
        arg_offsets = list(self._get_offsets(func_ast))
        for arg, ast_node, i in zip(args, func_ast.args, range(1000)):
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
                for l in range(start_line, end_line + 1):
                    start_ = start_col if l == start_line else 0
                    end_ = end_col if l == end_line else None
                    name_lines.append(
                        code_lines[l][start_:end_].strip(' ')
                    )
                yield self.output_class.arg_class(arg, name=' '.join(name_lines).strip(' ,'))
            else:
                yield self.output_class.arg_class(arg)

        kw_arg_names = {}
        for kw in func_ast.keywords:
            if isinstance(kw.value, ast.Name):
                kw_arg_names[kw.arg] = kw.value.id
        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name, variable=kw_arg_names.get(name))

    def _parse_code(self, call_frame, func_regex, filename) -> Tuple[Optional[ast.AST], Optional[List[str]], int]:
        call_lines = []
        for line in range(call_frame.index, -1, -1):
            new_line = call_frame.code_context[line]
            call_lines.append(new_line)
            if re.search(func_regex, new_line):
                break
        call_lines.reverse()
        lineno = call_frame.lineno - len(call_lines) + 1

        original_code = code = dedent(''.join(call_lines))
        func_ast = None
        tail_index = call_frame.index
        try:
            func_ast = ast.parse(code, filename=filename).body[0].value
        except SyntaxError as e1:
            # if the trailing bracket(s) of the function is/are on a new line eg.
            # debug(
            #     foo, bar,
            # )
            # inspect ignores it when setting index and we have to add it back
            for extra in range(2, 6):
                extra_lines = call_frame.code_context[tail_index + 1:tail_index + extra]
                code = dedent(''.join(call_lines + extra_lines))
                try:
                    func_ast = ast.parse(code).body[0].value
                except SyntaxError:
                    pass
                else:
                    break

            if not func_ast:
                if self._warnings:
                    warnings.warn('error passing code:\n"{}"\nError: {}'.format(original_code, e1), SyntaxWarning)
                return None, None, lineno

        if not isinstance(func_ast, ast.Call):
            if self._warnings:
                warnings.warn('error passing code, found {} not Call'.format(func_ast.__class__), SyntaxWarning)
            return None, None, lineno

        code_lines = [l for l in code.split('\n') if l]
        # this removes the trailing bracket from the lines of code meaning it doesn't appear in the
        # representation of the last argument
        code_lines[-1] = code_lines[-1][:-1]
        return func_ast, code_lines, lineno

    @classmethod
    def _get_offsets(cls, func_ast):
        for arg in func_ast.args:
            start_line, start_col = arg.lineno - 1, arg.col_offset

            # horrible hack for http://bugs.python.org/issue31241
            if isinstance(arg, (ast.ListComp, ast.GeneratorExp)):
                start_col -= 1
            yield start_line, start_col
        for kw in func_ast.keywords:
            yield kw.value.lineno - 1, kw.value.col_offset - len(kw.arg) - 1


debug = Debug()
