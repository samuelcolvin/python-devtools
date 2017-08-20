import ast
import inspect
import re
import warnings
from pathlib import Path
from textwrap import dedent
from typing import Generator, List

__all__ = ['Debug', 'debug']
CWD = Path('.').resolve()


class DebugArgument:
    __slots__ = 'value', 'name', 'extra'

    def __init__(self, value, *, name=None, **extra):
        self.value = value
        self.name = name
        self.extra = []
        if isinstance(value, (str, bytes)):
            self.extra.append(('len', len(value)))
        self.extra += [(k, v) for k, v in extra.items() if v is not None]

    def value_str(self):
        if isinstance(self.value, str):
            return '"{}"'.format(self.value)
        return str(self.value)

    def __str__(self) -> str:
        template = '{value} ({self.value.__class__.__name__}) {extra}'
        if self.name:
            template = '{self.name} = ' + template
        return template.format(
            self=self,
            value=self.value_str(),
            extra=' '.join('{}={}'.format(k, v) for k, v in self.extra)
        ).rstrip(' ')  # trailing space if extra is empty


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

    def __str__(self) -> str:
        template = '{s.filename}:{s.lineno} {s.frame}'
        if len(self.arguments) == 1:
            return (template + ': {a}').format(s=self, a=self.arguments[0])
        else:
            return (template + '\n  {a}').format(s=self, a='\n  '.join(str(a) for a in self.arguments))

    def __repr__(self) -> str:
        arguments = ' '.join(str(a) for a in self.arguments)
        return '<DebugOutput {s.filename}:{s.lineno} {s.frame} arguments: {a}>'.format(s=self, a=arguments)


class Debug:
    output_class = DebugOutput

    def __call__(self, *args, **kwargs):
        print(self._process(args, kwargs, r'debug *\('), flush=True)

    def format(self, *args, **kwargs):
        return self._process(args, kwargs, r'debug.format *\(')

    def _process(self, args, kwargs, func_regex):
        curframe = inspect.currentframe()
        frames = inspect.getouterframes(curframe, context=20)
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

        call_lines = []
        for line in range(call_frame.index, 0, -1):
            new_line = call_frame.code_context[line]
            call_lines.append(new_line)
            if re.search(func_regex, new_line):
                break
        call_lines.reverse()

        return self.output_class(
            filename=filename,
            lineno=call_frame.lineno - len(call_lines) + 1,
            frame=call_frame.function,
            arguments=list(self._process_args(call_lines, args, kwargs))
        )

    def _process_args(self, call_lines, args, kwargs) -> Generator[DebugArgument, None, None]:  # noqa: C901
        code = dedent(''.join(call_lines))
        # print(code)
        func_ast = ast.parse(code).body[0].value

        arg_offsets = list(self._get_offsets(func_ast))
        for arg, ast_node, i in zip(args, func_ast.args, range(1000)):
            if isinstance(ast_node, ast.Name):
                yield self.output_class.arg_class(arg, name=ast_node.id)
            elif isinstance(ast_node, (ast.Str, ast.Bytes, ast.Num, ast.List, ast.Dict, ast.Set)):
                yield self.output_class.arg_class(arg)
            elif isinstance(ast_node, (ast.Call, ast.Compare)):
                # TODO replace this hack with astor when it get's round to a new release
                end = -2
                try:
                    next_line, next_offset = arg_offsets[i + 1]
                    if next_line == ast_node.lineno:
                        end = next_offset
                except IndexError:
                    pass
                name = call_lines[ast_node.lineno - 1][ast_node.col_offset:end]
                yield self.output_class.arg_class(arg, name=name.strip(' ,'))
            else:
                warnings.warn('Unknown type: {}'.format(ast.dump(ast_node)), category=RuntimeError)
                yield self.output_class.arg_class(arg)

        kw_arg_names = {}
        for kw in func_ast.keywords:
            if isinstance(kw.value, ast.Name):
                kw_arg_names[kw.arg] = kw.value.id
        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name, variable=kw_arg_names.get(name))

    @classmethod
    def _get_offsets(cls, func_ast):
        for arg in func_ast.args:
            yield arg.lineno, arg.col_offset
        for kw in func_ast.keywords:
            yield kw.value.lineno, kw.value.col_offset - len(kw.arg) - 1


debug = Debug()
