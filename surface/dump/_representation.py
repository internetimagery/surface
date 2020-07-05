""" Build representational information from live objects """

from typing import NamedTuple

import re
import inspect
import logging
import contextlib

import sigtools

LOG = logging.getLogger(__name__)

INDENT = "    "
AnyStr = "typing.Any"

# Name format package.module:Class.method
name_split = re.compile(r"[\.:]").split

# Cli colours
magenta = "\033[35m{}\033[0m".format
cyan = "\033[36m{}\033[0m".format
green = "\033[32m{}\033[0m".format
yellow = "\033[33m{}\033[0m".format


def get_indent(num):
    # type: (int) -> str
    return INDENT * num


Import = NamedTuple("Import", [("path", str), ("name", str), ("alias", str)])


class BaseWrapper(object):
    def __init__(self, wrapped):
        # type: (Any) -> None
        """ Pull information from a live object to create a representation later """
        self._id = id(wrapped)
        self._repr = str(repr(wrapped)).replace("\n", " ")

    def get_id(self):
        # type: () -> int
        """ Ye olde ID """
        return self._id

    def get_imports(self, path, name):
        # type: (str, str) -> List[Import]
        """ Any imports required to be added for this. """
        return []

    def get_body(self, indent, path, name):
        # type: (int, str, str) -> str
        """ Export the representaton as a string suitable for insertion into a stubfile """
        return ""

    def get_cli(self, indent, path, name, colour):
        # type: (int, str, str, bool) -> str
        """ Export a representation as a string suitable for presentation in the command line """
        return ""


class Module(BaseWrapper):
    def __init__(self, module):
        # type: (types.ModuleType) -> None
        super(Module, self).__init__(module)
        self._name = module.__name__

    def get_name(self):
        # type: () -> str
        return self._name

    def get_imports(self, path, name):
        # type: (str, str) -> List[Import]

        if name == self._name:
            # We are imported by our full name.
            # eg:
            # - import module
            # - import package.module
            return [Import(name, "", "")]
        module_parts = self._name.rsplit(".", -1)
        if name == module_parts[-1]:
            # We are imported by module name from a package
            # eg:
            # - from package import module
            return [Import(module_parts[0], name, "")]
        # We must be imported and given an alias.
        # eg:
        # - import module as _alias
        # - from package import module as _alias
        if len(module_parts) == 1:
            return [Import(module_parts[0], "", name)]
        return [Import(module_parts[0], module_parts[-1], name)]

    def get_cli(self, indent, path, name, colour):
        return "{}{}: {}".format(
            get_indent(indent),
            name_split(name)[-1],
            green(self._name) if colour else self._name,
        )


class Class(BaseWrapper):
    def __init__(self, wrapped):
        # type: (type) -> None
        super(Class, self).__init__(wrapped)
        self._docstring = inspect.getdoc(wrapped) or ""
        self._definition = wrapped.__module__
        self._name = wrapped.__name__

    def get_name(self):
        # type: () -> str
        return self._name

    def get_definition(self):
        # type: () -> str
        return self._definition

    def get_imports(self, path, name):
        if self._definition == path:
            # We have the definition in this file
            return []
        if self._name == name:
            # - from package.module import class
            return [Import(self._definition, name, "")]
        # - from package.module import class as _alias
        if "." in name:
            name = "__{}".format(name_split(name)[-1])
        return [Import(self._definition, self._name, name)]

    def get_body(self, indent, path, name):
        if self._definition != path:
            # We are looking at a reference to the class
            # not the definition itself. The import method handles this.
            if name == self._name:
                return ""

            return "{}{}: {} = ... # {}".format(
                get_indent(indent),
                name_split(name)[-1],
                "__{}".format(name_split(name)[-1]) if "." in name else name,
                self._repr,
            )
        # TODO: get mro for subclasses
        return '{}class {}(object):\n{}""" {} """'.format(
            get_indent(indent),
            name_split(name)[-1],
            get_indent(indent + 1),
            "\n{}".format(get_indent(indent + 2)).join(self._docstring.splitlines()),
        )

    def get_cli(self, indent, path, name, colour):
        name = name_split(name)[-1]
        return "{}{} {}:".format(
            get_indent(indent),
            magenta("class") if colour else "class",
            cyan(name) if colour else name,
        )


Param = NamedTuple("Sig", [("name", str), ("type", str), ("prefix", str)])


class Function(BaseWrapper):
    def __init__(self, wrapped):
        super(Function, self).__init__(wrapped)
        self._parameters, self._returns = self._get_parameters(wrapped)

    def get_body(self, indent, path, name):
        # TODO: get signature information
        name = name_split(name)[-1]
        params = ", ".join(
            "{}{}: {}".format(p.prefix, p.name, p.type) for p in self._parameters
        )
        return "{}def {}({}) -> {}: ...".format(
            get_indent(indent),
            name,
            params,
            "None" if name == "__init__" else self._returns,
        )

    def get_imports(self, path, name):
        types = [Import(p.type.rsplit(".", 1)[0], "", "") for p in self._parameters]
        types.append(Import(self._returns.rsplit(".", 1)[0], "", ""))
        return types

    def get_cli(self, indent, path, name, colour):
        name = name_split(name)[-1]
        params = ", ".join(p.prefix + p.type for p in self._parameters)
        return "{}{} {}({}) -> {}".format(
            get_indent(indent),
            magenta("def") if colour else "def",
            cyan(name) if colour else name,
            green(params) if colour else params,
            green(AnyStr) if colour else AnyStr,
        )

    def _get_parameters(self, function):
        # type: (Callable) -> Tuple[Tuple[Param, ...], str]
        sig = self._get_signature(function)
        if not sig:
            return (Param("_args", AnyStr, "*"), Param("_kwargs", AnyStr, "**")), AnyStr
        params = tuple(
            Param(
                param.name,
                AnyStr,
                "*"
                if param.kind == param.VAR_POSITIONAL
                else "**"
                if param.kind == param.VAR_KEYWORD
                else "",
            )
            for param in sig.parameters.values()
        )
        returns = AnyStr
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


class Method(Function):
    pass


class ClassMethod(Function):
    def __init__(self, wrapped):
        super(ClassMethod, self).__init__(wrapped.__func__)

    def get_body(self, indent, path, name):
        return "{}@classmethod\n{}".format(
            get_indent(indent), super(ClassMethod, self).get_body(indent, path, name),
        )

    def get_cli(self, indent, path, name, colour):
        return "{}@{}\n{}".format(
            get_indent(indent),
            cyan("classmethod") if colour else "classmethod",
            super(ClassMethod, self).get_cli(indent, path, name, colour),
        )


class StaticMethod(Function):
    def __init__(self, wrapped):
        super(StaticMethod, self).__init__(wrapped.__func__)

    def get_body(self, indent, path, name):
        return "{}@staticmethod\n{}".format(
            get_indent(indent), super(StaticMethod, self).get_body(indent, path, name),
        )

    def get_cli(self, indent, path, name, colour):
        return "{}@{}\n{}".format(
            get_indent(indent),
            cyan("staticmethod") if colour else "staticmethod",
            super(StaticMethod, self).get_cli(indent, path, name, colour),
        )


class Attribute(BaseWrapper):
    def get_body(self, indent, path, name):
        return "{}{}: {} = ... # {}".format(
            get_indent(indent), name_split(name)[-1], AnyStr, self._repr
        )

    def get_imports(self, path, name):
        return [Import("typing", "", "")]

    def get_cli(self, indent, path, name, colour):
        return "{}{}: {}".format(
            get_indent(indent),
            name_split(name)[-1],
            green(AnyStr) if colour else AnyStr,
        )
