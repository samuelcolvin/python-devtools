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
    # 50 lines should be enough to make sure we always get the entire function definition
    frame_context_length = 50

    def __call__(self, *args, **kwargs):
        print(self._process(args, kwargs, r'debug *\('), flush=True)

    def format(self, *args, **kwargs):
        return self._process(args, kwargs, r'debug.format *\(')

    def _process(self, args, kwargs, func_regex):
        curframe = inspect.currentframe()
        frames = inspect.getouterframes(curframe, context=self.frame_context_length)
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
        # print(call_frame)
        # from pprint import pprint
        # pprint(call_frame.code_context)
        if call_frame.code_context:
            for line in range(call_frame.index, 0, -1):
                new_line = call_frame.code_context[line]
                call_lines.append(new_line)
                if re.search(func_regex, new_line):
                    break
            call_lines.reverse()
            lineno = call_frame.lineno - len(call_lines) + 1
        else:
            lineno = call_frame.lineno - len(call_lines)

        return self.output_class(
            filename=filename,
            lineno=lineno,
            frame=call_frame.function,
            arguments=list(self._process_args(call_lines, args, kwargs, call_frame))
        )

    def _args_inspection_failed(self, args, kwargs):
        for arg in args:
            yield self.output_class.arg_class(arg)
        for name, value in kwargs.items():
            yield self.output_class.arg_class(value, name=name)

    def _process_args(self, call_lines, args, kwargs, call_frame) -> Generator[DebugArgument, None, None]:  # noqa: C901
        if not call_lines:
            warnings.warn('no code context for debug call, code inspection impossible', RuntimeWarning)
            yield from self._args_inspection_failed(args, kwargs)
            return

        code = dedent(''.join(call_lines))
        # print(code)
        try:
            func_ast = ast.parse(code).body[0].value
        except SyntaxError as e1:
            # if the trailing bracket of the function is on a new line eg.
            # debug(
            #     foo, bar,
            # )
            # inspect ignores it with index and we have to add it back
            code2 = code + call_frame.code_context[call_frame.index + 1]
            try:
                func_ast = ast.parse(code2).body[0].value
            except SyntaxError:
                warnings.warn('error passing code:\n"{}"\nError: {}'.format(code, e1), SyntaxWarning)
                yield from self._args_inspection_failed(args, kwargs)
                return
            else:
                code = code2

        code_lines = [l for l in code.split('\n') if l]
        # this removes the trailing bracket from the lines of code meaning it doesn't appear in the
        # representation of the last argument
        code_lines[-1] = code_lines[-1][:-1]

        arg_offsets = list(self._get_offsets(func_ast))
        for arg, ast_node, i in zip(args, func_ast.args, range(1000)):
            if isinstance(ast_node, ast.Name):
                yield self.output_class.arg_class(arg, name=ast_node.id)
            elif isinstance(ast_node, (ast.Str, ast.Bytes, ast.Num, ast.List, ast.Dict, ast.Set)):
                yield self.output_class.arg_class(arg)
            elif isinstance(ast_node, (ast.Call, ast.Compare)):
                # TODO replace this hack with astor when it get's round to a new release
                start_line, start_col = ast_node.lineno - 1, ast_node.col_offset
                end_line, end_col = len(code_lines) - 1, None

                if i < len(arg_offsets) - 1:
                    end_line, end_col = arg_offsets[i + 1]

                name_lines = []
                for l in range(start_line, end_line + 1):
                    start_ = start_col if l == start_line else 0
                    end_ = end_col if l == end_line else None
                    name_lines.append(
                        code_lines[l][start_:end_].strip(' ')
                    )
                yield self.output_class.arg_class(arg, name=' '.join(name_lines).strip(' ,'))
            else:
                warnings.warn('Unknown type: {}'.format(ast.dump(ast_node)), RuntimeWarning)
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
            yield arg.lineno - 1, arg.col_offset
        for kw in func_ast.keywords:
            yield kw.value.lineno - 1, kw.value.col_offset - len(kw.arg) - 1


debug = Debug()
