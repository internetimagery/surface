""" Build representational information from live objects """

from typing import NamedTuple

import re
import inspect
import logging
import keyword
import contextlib

import sigtools

LOG = logging.getLogger(__name__)

INDENT = "    "
NAME_REG = re.compile(r"([\w\.]+)\.\w+")

BAD_NAME = re.compile("^(None|\d+|{})$".format("|".join(keyword.kwlist)))

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


def safe_name(name):
    # type: (str) -> str
    if BAD_NAME.match(name):
        return name
    return name + "_"


Import = NamedTuple("Import", [("path", str), ("name", str), ("alias", str)])


class BaseWrapper(object):
    def __init__(self, wrapped, parent, plugin):
        # type: (Any, Optional[Any], PluginManager) -> None
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
    def __init__(self, module, parent, plugin):
        # type: (types.ModuleType, Optional[Any], PluginManager) -> None
        super(Module, self).__init__(module, parent, plugin)
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
    def __init__(self, wrapped, parent, plugin):
        # type: (type, OPtional[Any], PluginManager) -> None
        super(Class, self).__init__(wrapped, parent, plugin)
        self._docstring = (inspect.getdoc(wrapped) or "").replace('"""', "'''")
        self._definition = wrapped.__module__
        self._name = safe_name(wrapped.__name__)

    def get_name(self):
        # type: () -> str
        return self._name

    def get_definition(self):
        # type: () -> str
        return self._definition

    def get_imports(self, path, name):
        name = safe_name(name)
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
    def __init__(self, wrapped, parent, plugin):
        super(Function, self).__init__(wrapped, parent, plugin)
        self._parameters, self._returns = plugin.types_from_function(wrapped, parent)
        try:
            self._module = wrapped.__module__
        except AttributeError:
            self._module = None

    def get_body(self, indent, path, name):
        if self._module and path != self._module:
            return "{}{}: {} = {}.{}".format(
                get_indent(indent),
                name_split(name)[-1],
                "typing.Callable[[{}], {}]".format(
                    ", ".join(p.type for p in self._parameters), self._returns,
                ),
                self._module,
                name,
            )
        name = safe_name(name_split(name)[-1])
        return "{}def {}({}) -> {}: ...".format(
            get_indent(indent),
            name,
            ", ".join(p.as_arg() for p in self._parameters),
            "None" if name == "__init__" else self._returns,
        )

    def get_imports(self, path, name):
        types = []
        for p in self._parameters:
            for match in NAME_REG.finditer(p.type):
                types.append(Import(match.group(1), "", ""))

        for match in NAME_REG.finditer(self._returns):
            types.append(Import(match.group(1), "", ""))
        return types

    def get_cli(self, indent, path, name, colour):
        name = safe_name(name_split(name)[-1])
        params = ", ".join(p.as_cli() for p in self._parameters)
        return "{}{} {}({}) -> {}".format(
            get_indent(indent),
            magenta("def") if colour else "def",
            cyan(name) if colour else name,
            green(params) if colour else params,
            green(self._returns) if colour else self._returns,
        )


class Method(Function):
    pass


class ClassMethod(Function):
    def __init__(self, wrapped, parent, plugin):
        super(ClassMethod, self).__init__(wrapped.__func__, parent, plugin)

    def get_body(self, indent, path, name):
        body = super(ClassMethod, self).get_body(indent, path, name)
        if self._module and path != self._module:
            return body
        return "{}@classmethod\n{}".format(get_indent(indent), body,)

    def get_cli(self, indent, path, name, colour):
        return "{}@{}\n{}".format(
            get_indent(indent),
            cyan("classmethod") if colour else "classmethod",
            super(ClassMethod, self).get_cli(indent, path, name, colour),
        )


class StaticMethod(Function):
    def __init__(self, wrapped, parent, plugin):
        super(StaticMethod, self).__init__(wrapped.__func__, parent, plugin)

    def get_body(self, indent, path, name):
        body = super(StaticMethod, self).get_body(indent, path, name)
        if self._module and path != self._module:
            return body
        return "{}@staticmethod\n{}".format(get_indent(indent), body,)

    def get_cli(self, indent, path, name, colour):
        return "{}@{}\n{}".format(
            get_indent(indent),
            cyan("staticmethod") if colour else "staticmethod",
            super(StaticMethod, self).get_cli(indent, path, name, colour),
        )


class Property(Function):
    def __init__(self, wrapped, parent, plugin):
        super(Property, self).__init__(wrapped.fget, parent, plugin)

    def get_body(self, indent, path, name):
        return "{}{}: {} = ... # {}".format(
            get_indent(indent),
            safe_name(name_split(name)[-1]),
            self._returns,
            self._repr,
        )

    def get_imports(self, path, name):
        types = [
            Import(match.group(1), "", "") for match in NAME_REG.finditer(self._returns)
        ]
        return types

    def get_cli(self, indent, path, name, colour):
        return "{}{}: {}".format(
            get_indent(indent),
            safe_name(name_split(name)[-1]),
            green(self._returns) if colour else self._returns,
        )


class Attribute(BaseWrapper):
    def __init__(self, wrapped, parent, plugin):
        super(Attribute, self).__init__(wrapped, parent, plugin)
        self._type = plugin.type_from_value(wrapped, parent)

    def get_body(self, indent, path, name):
        return "{}{}: {} = ... # {}".format(
            get_indent(indent), safe_name(name_split(name)[-1]), self._type, self._repr
        )

    def get_imports(self, path, name):
        types = [
            Import(match.group(1), "", "") for match in NAME_REG.finditer(self._type)
        ]
        return types

    def get_cli(self, indent, path, name, colour):
        return "{}{}: {}".format(
            get_indent(indent),
            safe_name(name_split(name)[-1]),
            green(self._type) if colour else self._type,
        )
