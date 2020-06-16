import os
import sys

from .ansi import sformat
from .prettier import PrettyFormat
from .timer import Timer
from .utils import env_bool, env_true, use_highlight

__all__ = 'Debug', 'debug'
MYPY = False
if MYPY:
    import ast
    from types import FrameType
    from typing import Generator, List, Optional, Tuple


pformat = PrettyFormat(
    indent_step=int(os.getenv('PY_DEVTOOLS_INDENT', 4)),
    simple_cutoff=int(os.getenv('PY_DEVTOOLS_SIMPLE_CUTOFF', 10)),
    width=int(os.getenv('PY_DEVTOOLS_WIDTH', 120)),
    yield_from_generators=env_true('PY_DEVTOOLS_YIELD_FROM_GEN', True),
)


class IntrospectionError(ValueError):
    pass


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

    def __init__(self, *, filename: str, lineno: int, frame: str, arguments: 'List[DebugArgument]', warning=None):
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

    def __init__(
        self, *, warnings: 'Optional[bool]' = None, highlight: 'Optional[bool]' = None, frame_context_length: int = 50
    ):
        self._show_warnings = env_bool(warnings, 'PY_DEVTOOLS_WARNINGS', True)
        self._highlight = highlight
        # 50 lines should be enough to make sure we always get the entire function definition
        self._frame_context_length = frame_context_length

    def __call__(self, *args, file_=None, flush_=True, **kwargs) -> None:
        d_out = self._process(args, kwargs, 'debug')
        s = d_out.str(use_highlight(self._highlight, file_))
        print(s, file=file_, flush=flush_)

    def format(self, *args, **kwargs) -> DebugOutput:
        return self._process(args, kwargs, 'format')

    def breakpoint(self):
        import pdb

        pdb.Pdb(skip=['devtools.*']).set_trace()

    def timer(self, name=None, *, verbose=True, file=None, dp=3) -> Timer:
        return Timer(name=name, verbose=verbose, file=file, dp=dp)

    def _process(self, args, kwargs, func_name: str) -> DebugOutput:
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

        filename = call_frame.f_code.co_filename
        function = call_frame.f_code.co_name
        if filename.startswith('/'):
            # make the path relative
            from pathlib import Path

            cwd = Path('.').resolve()
            try:
                filename = str(Path(filename).relative_to(cwd))
            except ValueError:
                # happens if filename path is not within CWD
                pass

        lineno = call_frame.f_lineno
        warning = None

        import inspect

        try:
            file_lines, _ = inspect.findsource(call_frame)
        except OSError:
            warning = 'no code context for debug call, code inspection impossible'
            arguments = list(self._args_inspection_failed(args, kwargs))
        else:
            try:
                first_line, last_line = self._statement_range(call_frame, func_name)
                func_ast, code_lines = self._parse_code(filename, file_lines, first_line, last_line)
            except IntrospectionError as e:
                # parsing failed
                warning = e.args[0]
                arguments = list(self._args_inspection_failed(args, kwargs))
            else:
                arguments = list(self._process_args(func_ast, code_lines, args, kwargs))

        return self.output_class(
            filename=filename,
            lineno=lineno,
            frame=function,
            arguments=arguments,
            warning=self._show_warnings and warning,
        )

    def _args_inspection_failed(self, args, kwargs):
        for arg in args:
            yield self.output_class.arg_class(arg)
        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name)

    def _process_args(self, func_ast, code_lines, args, kwargs) -> 'Generator[DebugArgument, None, None]':  # noqa: C901
        import ast

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
            elif isinstance(ast_node, complex_nodes):
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
        self, filename: str, file_lines: 'List[str]', first_line: int, last_line: int
    ) -> 'Tuple[ast.AST, List[str]]':
        """
        All we're trying to do here is build an AST of the function call statement. However numerous ugly interfaces,
        lack on introspection support and changes between python versions make this extremely hard.
        """
        from textwrap import dedent
        import ast

        def get_code(_last_line: int) -> str:
            lines = file_lines[first_line - 1 : _last_line]
            return dedent(''.join(ln for ln in lines if ln.strip('\n ') and not ln.lstrip(' ').startswith('#')))

        code = get_code(last_line)
        func_ast = None
        try:
            func_ast = self._wrap_parse(code, filename)
        except (SyntaxError, AttributeError) as e1:
            # if the trailing bracket(s) of the function is/are on a new line e.g.:
            # debug(
            #     foo, bar,
            # )
            # inspect ignores it when setting index and we have to add it back
            for extra in range(1, 6):
                code = get_code(last_line + extra)
                try:
                    func_ast = self._wrap_parse(code, filename)
                except (SyntaxError, AttributeError):
                    pass
                else:
                    break

            if not func_ast:
                raise IntrospectionError('error parsing code, {0.__class__.__name__}: {0}'.format(e1))

        if not isinstance(func_ast, ast.Call):
            raise IntrospectionError('error parsing code, found {0.__class__} not Call'.format(func_ast))

        code_lines = [line for line in code.split('\n') if line]
        # this removes the trailing bracket from the lines of code meaning it doesn't appear in the
        # representation of the last argument
        code_lines[-1] = code_lines[-1][:-1]
        return func_ast, code_lines

    @staticmethod  # noqa: C901
    def _statement_range(call_frame: 'FrameType', func_name: str) -> 'Tuple[int, int]':  # noqa: C901
        """
        Try to find the start and end of a frame statement.
        """
        import dis

        # dis.disassemble(call_frame.f_code, call_frame.f_lasti)
        # pprint([i for i in dis.get_instructions(call_frame.f_code)])

        instructions = iter(dis.get_instructions(call_frame.f_code))
        first_line = None
        last_line = None

        for instr in instructions:  # pragma: no branch
            if instr.starts_line:
                if instr.opname in {'LOAD_GLOBAL', 'LOAD_NAME'} and instr.argval == func_name:
                    first_line = instr.starts_line
                elif instr.opname == 'LOAD_GLOBAL' and instr.argval == 'debug':
                    if next(instructions).argval == func_name:
                        first_line = instr.starts_line
            if instr.offset == call_frame.f_lasti:
                break

        if first_line is None:
            raise IntrospectionError('error parsing code, unable to find "{}" function statement'.format(func_name))

        for instr in instructions:
            if instr.starts_line:
                last_line = instr.starts_line - 1
                break

        if last_line is None:
            if sys.version_info >= (3, 8):
                # absolutely no reliable way of getting the last line of the statement, complete hack is to
                # get the last line of the last statement of the whole code block and go from there
                # this assumes (perhaps wrongly?) that the reason we couldn't find last_line is that the statement
                # in question was the last of the block
                last_line = max(i.starts_line for i in dis.get_instructions(call_frame.f_code) if i.starts_line)
            else:
                # in older version of python f_lineno is the end of the statement, not the beginning
                # so this is a reasonable guess
                last_line = call_frame.f_lineno

        return first_line, last_line

    @staticmethod
    def _wrap_parse(code: str, filename: str) -> 'ast.Call':
        """
        async wrapper is required to avoid await calls raising a SyntaxError
        """
        import ast
        from textwrap import indent

        code = 'async def wrapper():\n' + indent(code, ' ')
        return ast.parse(code, filename=filename).body[0].body[0].value

    @staticmethod
    def _get_offsets(func_ast):
        import ast

        for arg in func_ast.args:
            start_line, start_col = arg.lineno - 2, arg.col_offset - 1

            # horrible hack for http://bugs.python.org/issue31241
            if isinstance(arg, (ast.ListComp, ast.GeneratorExp)):
                start_col -= 1
            yield start_line, start_col
        for kw in func_ast.keywords:
            yield kw.value.lineno - 2, kw.value.col_offset - 2 - (len(kw.arg) if kw.arg else 0)


debug = Debug()
