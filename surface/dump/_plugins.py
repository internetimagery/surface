from typing import _type_repr, Any

import re
import logging
import inspect
import token
import tokenize
import contextlib

import sigtools

from surface.dump._docstring import parse_docstring

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

LOG = logging.getLogger(__name__)

AnyStr = _type_repr(Any)


class Param(object):
    __slots__ = ("name", "type", "kind")

    POSITIONAL_OR_KEYWORD = 0
    POSITIONAL_OR_KEYWORD_WITH_DEFAULT = 1
    POSITIONAL_ONLY = 2
    KEYWORD_ONLY = 3
    VAR_POSITIONAL = 4
    VAR_KEYWORD = 5

    def __init__(self, name, type_, kind):
        # type: (str, str, int) -> None
        self.name = name
        self.type = type_
        self.kind = kind

    def as_arg(self):
        # type: () -> str
        name = self._get_variadic_prefix() + self.name
        type_ = ": {}".format(self.type) if self.type else ""
        default = " = ..." if self.kind in (self.POSITIONAL_OR_KEYWORD_WITH_DEFAULT, self.KEYWORD_ONLY) else ""
        return name + type_ + default

    def as_cli(self):
        # type: () -> str
        return self.as_arg()
    
    def _get_variadic_prefix(self):
        return (
            "*"
            if self.kind == self.VAR_POSITIONAL
            else "**"
            if self.kind == self.VAR_KEYWORD
            else ""
        )


class BasePlugin(object):
    """ Abstraction to collect typing information from live objects """

    def types_from_function(self, function, parent, sig):
        # type: (Callable, Optional[Any], Optional[sigtools.Signature]]) -> Optional[Tuple[List[Param], str]
        pass

    def type_from_value(self, value, parent):
        # type: (Any, Optional[Any]) -> Optional[str]
        pass

    @staticmethod
    def _sig_param_kind_map(param):
        # type: (sigtools.Param) -> int
        """ Utility to map sigtools.Param kind to Param kind """
        if param.kind == param.POSITIONAL_OR_KEYWORD:
            if param.default is param.empty:
                return Param.POSITIONAL_OR_KEYWORD
            return Param.POSITIONAL_OR_KEYWORD_WITH_DEFAULT
        if param.kind == param.POSITIONAL_ONLY:
            return Param.POSITIONAL_ONLY
        if param.kind == param.KEYWORD_ONLY:
            return Param.KEYWORD_ONLY
        if param.kind == param.VAR_POSITIONAL:
            return Param.VAR_POSITIONAL
        if param.kind == param.VAR_KEYWORD:
            return Param.VAR_KEYWORD
        raise ValueError("Unknown parameter {}".format(param.kind))

    @staticmethod
    def _get_default_type(param):
        # type: (sigtools.Parameter) -> str
        if param.name in ("self", "cls") and param.kind == param.POSITIONAL_ONLY:
            return ""
        return AnyStr


class PluginManager(object):
    def __init__(self, plugins):
        # type: (List[BasePlugin]) -> None
        self._plugins = plugins

    def types_from_function(self, function, parent):
        # type: (Callable, Optional[Any]) -> Tuple[List[Param], str]
        sig = self._get_signature(function)
        for plugin in self._plugins:
            params = plugin.types_from_function(function, parent, sig)
            if params:
                return params
        if not sig:
            return (
                [
                    Param("_args", AnyStr, Param.VAR_POSITIONAL),
                    Param("_kwargs", AnyStr, Param.VAR_KEYWORD),
                ],
                AnyStr,
            )
        return (
            [
                Param(param.name, BasePlugin._get_default_type(param), BasePlugin._sig_param_kind_map(param))
                for param in sig.parameters.values()
            ],
            AnyStr,
        )

    def type_from_value(self, value, parent):
        # type: (Any, Optional[Any]) -> str
        for plugin in self._plugins:
            type_ = plugin.type_from_value(value, parent)
            if type_:
                return type_
        return AnyStr

    def _get_signature(self, function):
        # type: (Callable) -> Optional[sigtools.Signature]
        with self._fix_annotation(function):
            try:
                sig = sigtools.signature(function)
            except (ValueError, OSError):
                # Can't find a signature for a function. Acceptable failure.
                LOG.debug("Could not find signature for %s", function)
            except SyntaxError:
                # Could not parse the source code. This can happen for any number of reasons.
                # Quality of the source code is not our concern here. Let it slide.
                LOG.debug("Failed to read function source %s", function)
            except RuntimeError:
                # TypeError?
                # RuntimeError: https://github.com/epsy/sigtools/issues/10
                LOG.exception("Failed to get signature for {}".format(function))
            else:
                return sig
            return None
    
    @staticmethod
    @contextlib.contextmanager
    def _fix_annotation(func):
        # type: (Callable) -> None
        """ Sanitize annotations to prevent errors """
        try:
            annotations = func.__annotations__
        except AttributeError:
            fixup = False
        else:
            fixup = not isinstance(annotations, dict)
            if fixup:
                func.__annotations__ = {}
        try:
            yield
        finally:
            if fixup:
                func.__annotations__ = annotations


class AnnotationTypingPlugin(BasePlugin):
    def type_from_value(self, value, parent):
        # type: (Any, Optional[Any]) -> Optional[str]
        for name, item in inspect.getmembers(parent):
            if item is value:
                try:
                    annotation = parent.__annotations__[name]
                except (AttributeError, KeyError, TypeError):
                    pass
                else:
                    return _type_repr(annotation)
                break
        return None

    def types_from_function(self, function, parent, sig):
        # type: (Callable, Optional[Any], Optional[sigtools.Signature]]) -> Optional[Tuple[List[Param], str]]
        if not sig:
            return None
        if (
            all(p.annotation is sig.empty for p in sig.parameters.values())
            and sig.return_annotation is sig.empty
        ):
            return None

        params = tuple(
            Param(
                param.name,
                _type_repr(param.annotation)
                if param.annotation is not sig.empty
                else self._get_default_type(param),
                self._sig_param_kind_map(param),
            )
            for param in sig.parameters.values()
        )
        returns = (
            AnyStr
            if sig.return_annotation is sig.empty
            else _type_repr(sig.return_annotation)
        )
        return params, returns


class CommentTypingPlugin(BasePlugin):
    """ Abstraction to collect typing information from typing comments """

    TYPE_REG = r"[\w\.\[\]\,\s]+"
    SINGLE_REG = re.compile(r"\**\w+(\[{}\])?".format(TYPE_REG))
    PREFIX_REG = r"#\s*type:\s+"
    ATTR_REG = re.compile("{}({})".format(PREFIX_REG, TYPE_REG))
    FUNC_REG = re.compile(
        r"{prefix}\(({type_})?\)\s+->\s+({type_})".format(
            prefix=PREFIX_REG, type_=TYPE_REG
        )
    )

    def types_from_function(self, function, parent, sig):
        # type: (Callable, Optional[Any], Optional[sigtools.Signature]) -> Optional[Tuple[List[Param], str]]
        if not sig:
            return None
        try:
            code = inspect.getsource(function)
        except (OSError, TypeError, IOError):
            return None
        lines = code.splitlines(True)
        lines_iter = iter(lines)
        tokens = list(tokenize.generate_tokens(lambda: next(lines_iter)))
        args = []
        returns = None
        for i, tok in enumerate(tokens):
            if tok[0] == tokenize.NL:
                if tokens[i - 1][0] != tokenize.COMMENT:
                    continue
                match = self.ATTR_REG.match(tokens[i - 1][1])
                if not match:
                    continue
                args.append(match.group(1))
            elif tok[0] == token.NEWLINE:
                if tokens[i - 1][0] == tokenize.COMMENT:
                    comment = tokens[i - 1][1]
                elif tokens[i + 1][0] == tokenize.COMMENT:
                    comment = tokens[i + 1][1]
                else:
                    continue
                match = self.FUNC_REG.match(comment)
                if not match:
                    continue
                if match.group(1) and match.group(1).strip() != "...":
                    args = self._split_args(match.group(1))
                returns = match.group(2).strip()
                break

        if returns is None:
            return None

        params = [
            Param(name, arg.strip() if arg is not None else self._get_default_type(param), self._sig_param_kind_map(p))
            for (name, p), arg in zip_longest(
                reversed(sig.parameters.items()), reversed(args), fillvalue=None
            )
        ]
        return list(reversed(params)), returns

    @staticmethod
    def _split_args(string):
        # type: (str) -> List[str]
        level = 0
        section = ""
        sections = []
        for char in string:
            if char == "[":
                level += 1
            if char == "]":
                level -= 1
            if char == "," and not level:
                sections.append(section.strip())
                section = ""
                continue
            section += char
        sections.append(section.strip())
        return sections


class DocstringTypingPlugin(BasePlugin):
    def types_from_function(self, function, parent, sig):
        # type: (Callable, Optional[Any], Optional[sigtools.Signature]) -> Optional[Tuple[List[Param], str]]
        docstring = inspect.getdoc(function)
        if not docstring:
            return None
        parsed = parse_docstring(docstring)
        if not parsed:
            return None
        if sig:
            # If we could determine the signature, then use that information to guide us.
            params = [
                Param(
                    param.name,
                    parsed[0].get(param.name, self._get_default_type(param)),
                    self._sig_param_kind_map(param),
                )
                for param in sig.parameters.values()
            ]
            return params, parsed[1]
        
        # If we cannot discover the signature. We can only assume the docstring information is accurate.
        params = [
            Param(
                name,
                type_,
                Param.POSITIONAL_OR_KEYWORD,
            )
            for name, type_ in parsed[0].items()
        ]
        if inspect.isclass(parent):
            for attr in inspect.classify_class_attrs(parent):
                if attr.object is not function:
                    continue
                if attr.kind == "method":
                    params.insert(0, Param("self", "", Param.POSITIONAL_ONLY))
                if attr.kind == "class method":
                    params.insert(0, Param("cls", "", Param.POSITIONAL_ONLY))
                break
        return params, parsed[1]