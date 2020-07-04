""" Build representational information from live objects """

from typing import NamedTuple

import re
import inspect

INDENT = "    "

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


class Function(BaseWrapper):
    def get_body(self, indent, path, name):
        # TODO: get signature information
        name = name_split(name)[-1]
        return "{}def {}(*args: Any, **kwargs: Any) -> {}: ...".format(
            get_indent(indent),
            name,
            "None" if name == "__init__" else "Any",
        )
    
    def get_imports(self, path, name):
        return [Import("typing", "Any", "")]

    def get_cli(self, indent, path, name, colour):
        name = name_split(name)[-1]
        return "{}{} {}({}) -> {}".format(
            get_indent(indent),
            magenta("def") if colour else "def",
            cyan(name) if colour else name,
            green("*Any, **Any") if colour else "*Any, **Any",
            green("Any") if colour else "Any",
        )


class Method(Function):
    pass


class ClassMethod(Function):
    pass


class StaticMethod(Function):
    pass


class Attribute(BaseWrapper):
    def get_body(self, indent, path, name):
        return "{}{}: Any = ... # {}".format(get_indent(indent), name_split(name)[-1], self._repr)

    def get_imports(self, path, name):
        return [Import("typing", "Any", "")]

    def get_cli(self, indent, path, name, colour):
        return "{}{}: {}".format(
            get_indent(indent),
            name_split(name)[-1],
            green("Any") if colour else "Any",
        )
