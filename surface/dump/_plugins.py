from typing import _type_repr, Any

import re
import logging
import inspect
import token
import tokenize
import contextlib

import sigtools

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

LOG = logging.getLogger(__name__)

AnyStr = _type_repr(Any)


class Param(object):
    __slots__ = ("name", "type", "kind")

    VAR_POSITIONAL = 1
    VAR_KEYWORD = 2

    def __init__(self, name, type_, kind):
        # type: (str, str, int) -> None
        self.name = name
        self.type = type_
        self.kind = kind

    def as_arg(self):
        # type: () -> str
        prefix = "*" if self.kind == self.VAR_POSITIONAL else "**" if self.kind == self.VAR_KEYWORD else ""
        return "{}{}: {}".format(prefix, self.name, self.type)
    
    def as_cli(self):
        # type: () -> str
        prefix = "*" if self.kind == self.VAR_POSITIONAL else "**" if self.kind == self.VAR_KEYWORD else ""
        return prefix + self.type


class BasePlugin(object):
    """ Abstraction to collect typing information from live objects """

    def types_from_function(self, function, parent, sig):
        # type: (Callable, Optional[Any], Optional[sigtools.Signature]]) -> Optional[Tuple[List[Param], str]
        pass

    def type_from_value(self, value, parent):
        # type: (Any, Optional[Any]) -> Optional[str]
        pass


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
        return [Param("_args", AnyStr, Param.VAR_POSITIONAL), Param("_kwargs", AnyStr, Param.VAR_KEYWORD)], AnyStr

    def type_from_value(self, value, parent):
        # type: (Any Optional[Any]) -> str
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
            except ValueError:
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
                AnyStr
                if param.annotation is sig.empty
                else _type_repr(param.annotation),
                Param.VAR_POSITIONAL
                if param.kind == param.VAR_POSITIONAL
                else Param.VAR_KEYWORD
                if param.kind == param.VAR_KEYWORD
                else 0,
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
    SINGLE_REG = re.compile(r"\w+(\[{}\])?".format(TYPE_REG))
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
        except TypeError:
            return None
        lines = code.splitlines(True)
        tokens = list(tokenize.generate_tokens(iter(lines).__next__))
        args = []
        returns = AnyStr
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
                    args = [
                        arg.group(0).strip()
                        for arg in self.SINGLE_REG.finditer(match.group(1))
                    ]
                returns = match.group(2).strip()
                break

        params = [
            Param(
                name,
                arg.strip(),
                Param.VAR_POSITIONAL
                if p.kind == p.VAR_POSITIONAL
                else Param.VAR_KEYWORD
                if p.kind == p.VAR_KEYWORD
                else 0,
            )
            for (name, p), arg in zip_longest(
                reversed(sig.parameters.items()), reversed(args), fillvalue=AnyStr
            )
        ]
        return list(reversed(params)), returns
