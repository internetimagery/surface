from typing import _type_repr, Any

import logging
import inspect
import contextlib

import sigtools

LOG = logging.getLogger(__name__)

AnyStr = _type_repr(Any)


class Param(object):
    __slots__ = ("name", "type", "prefix")

    def __init__(self, name, type_="", prefix=""):
        # type: (str, str, str) -> None
        self.name = name
        self.type = type_
        self.prefix = prefix

    def as_arg(self):
        # type: () -> str
        return "{}{}: {}".format(self.prefix, self.name, self.type)


class BasePlugin(object):
    """ Abstraction to collect typing information from live objects """

    def types_from_function(self, function, parent):
        # type: (Callable, Optional[Any]) -> Optional[Tuple[List[Param], str]]
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
        for plugin in self._plugins:
            params = plugin.types_from_function(function, parent)
            if params:
                return params
        return [Param("_args", AnyStr, "*"), Param("_kwargs", AnyStr, "**")], AnyStr

    def type_from_value(self, value, parent):
        # type: (Any Optional[Any]) -> str
        for plugin in self._plugins:
            type_ = plugin.type_from_value(value, parent)
            if type_:
                return type_
        return AnyStr


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

    def types_from_function(self, function, parent):
        # type: (Callable, Optional[Any]) -> Optional[Tuple[List[Param], str]]
        sig = self._get_signature(function)
        if not sig:
            return None
        params = tuple(
            Param(
                param.name,
                AnyStr
                if param.annotation is sig.empty
                else _type_repr(param.annotation),
                "*"
                if param.kind == param.VAR_POSITIONAL
                else "**"
                if param.kind == param.VAR_KEYWORD
                else "",
            )
            for param in sig.parameters.values()
        )
        returns = (
            AnyStr
            if sig.return_annotation is sig.empty
            else _type_repr(sig.return_annotation)
        )
        return params, returns

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
