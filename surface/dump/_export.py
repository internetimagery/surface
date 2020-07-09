""" Export out data as stub files """


import os
import importlib
import collections

from pyhike import TrailBlazer

from surface.dump._representation import Class, Module, Function
from surface.dump._traversal import Representation, RepresentationBuilder

PATH_BLACKLIST = set(("builtins", "__builtin__"))

STUB_HEADER = (
    "# Automatically generated stub file; "
    "Generated by 'surface' (pip install surface).\n"
    "# Module: {}\n\n"
)


class Exporter(object):
    """
    Export subfiles from live imports
    
    >>> exporter = Exporter(modules=["os", "sys"])
    >>> exporter.export("/path/to/directory")
    """

    def __init__(self, modules=None, files=None, directories=None):
        # type: (Optional[Sequence[types.ModuleType]], Optional[Sequence[str]], Optional[Sequence[str]]) -> None
        self._modules = modules or []
        self._files = files or []
        self._directories = directories or []
        self._representation = None

    def get_representation(self):
        # type: () -> Representation
        if self._representation is None:
            added_modules = set()
            builder = RepresentationBuilder(added_modules)
            traveler = TrailBlazer(builder)
            for module in self._modules:
                added_modules.add(module.__name__)
                traveler.roam_module(module, module.__name__)
            for file_ in self._files:
                added_modules.add(os.path.basename(file_).split(".", 1)[0])
                traveler.roam_file(file_)
            for directory_ in self._directories:
                traveler.roam_directory(directory_)
            traveler.hike()
            representation = builder.get_representation()
            self._representation = filter_representation(representation)
        return self._representation

    def export(self, directory):
        # type: (str) -> Representation
        if not os.path.isdir(directory):
            raise ValueError("This is not a directory: {}".format(directory))
        representation = self.get_representation()
        export_stubs(representation, directory)
        return representation


def export_stubs(representation, directory):
    # type: (Representation) -> Representation
    """ Build a stubfile structure from the provided information """
    # Build skeleton files, to later fill with content
    files = build_skeleton_files(representation, directory)

    # Fill in the content of a file
    for path, contents in representation.items():
        with open(files[path], "w") as fh:
            fh.write(build_content(path, contents))
    return representation


def build_content(path, contents):
    # type: (str, Dict[str, BaseWrapper]) -> str
    """ Generate the content within the stub file """

    import_block = []
    body_block = []
    indent_stack = []
    # Walk from shortest to longest
    for name in sorted(contents):
        # If we leave an indented block, drop down
        while indent_stack:
            if name.startswith(indent_stack[-1]):
                break
            indent_stack.pop()

        node = contents[name]
        import_block.extend(node.get_imports(path, name))
        body_block.append(node.get_body(len(indent_stack), path, name))

        # If we are a class, enter an indented block
        if isinstance(node, Class):
            indent_stack.append(name + ".")

    return "{}\n\n{}\n\n{}".format(
        build_header(path),
        build_import_block(import_block),
        build_body_block(body_block),
    )


def build_header(path):
    # type: (str) -> str
    return STUB_HEADER.format(path)


def build_body_block(body_block):
    # type: (List[str]) -> str
    return "\n\n".join(body for body in body_block if body)


def build_import_block(import_block):
    # type: (List[Import]) -> str
    if not import_block:
        return ""

    imports = set()
    from_imports = collections.defaultdict(set)

    # Sort import types
    for import_ in import_block:
        if import_.path in PATH_BLACKLIST:
            continue
        if import_.name:
            # from package import module as _module
            from_imports[import_.path].add(import_)
        else:
            # import package.module
            imports.add(import_)

    # Build out our block
    import_lines = []
    alias = "{} as {}".format
    for import_ in sorted(imports):
        import_lines.append(
            "import {}".format(
                alias(import_.path, import_.alias) if import_.alias else import_.path
            )
        )
    for path in sorted(from_imports):
        import_line = (
            alias(import_.name, import_.alias) if import_.alias else import_.name
            for import_ in from_imports[path]
        )
        import_lines.append(
            "from {} import {}".format(path, ", ".join(sorted(import_line)))
        )
    return "\n".join(import_lines)


def build_skeleton_files(paths, directory):
    # type: (Collection[str], str) -> Dict[str, str]
    """ Build files out. Empty at this stage. Ready to be filled with stub content """
    structures = {}
    for path in sorted(paths, reverse=True):
        if path in structures:
            continue

        sections = path.split(".")
        for i in range(1, len(sections)):
            subsection = sections[:i]
            key = ".".join(subsection)
            if key in structures:
                continue
            package = os.path.join(directory, *subsection)
            init = os.path.join(package, "__init__.pyi")
            if not os.path.isfile(init):
                os.mkdir(package)
                with open(init, "w") as fh:
                    fh.write(build_header(key))
            structures[key] = init
        module = os.path.join(directory, *sections) + ".pyi"
        if not os.path.isfile(module):
            with open(module, "w") as fh:
                fh.write(build_header(path))
        structures[path] = module
    return structures


def filter_representation(representation):
    # type: (Representation) -> Representation
    """ Pull imported modules into their own file """
    new_representation = collections.defaultdict(dict)
    for path, contents in representation.items():
        module_map = {}
        # We need to read this shortest to longest.
        # Least specific to most.
        for qualname in sorted(contents):
            node = contents[qualname]
            new_path = path
            new_qualname = qualname

            # If a value belongs to an imported module, move it into there
            # We need to read this from longest to shortest (most specific to least)
            for prefix in sorted(module_map, reverse=True):
                if qualname.startswith(prefix):
                    new_path, new_prefix = module_map[prefix]
                    new_qualname = new_prefix + qualname[len(prefix) :]
                    break

            # If an imported module is found. Mark it, and we'll create a new stub for it
            if isinstance(node, Module):
                module_map[qualname + "."] = (node.get_name(), "")

            # If an imported class is found. Mark it too, and we'll create the definition stub.
            if (
                isinstance(node, (Class, Function))
                and node.get_definition()
                and path != node.get_definition()
            ):
                module_map[qualname + "."] = (
                    node.get_definition(),
                    node.get_name() + ".",
                )
                # Duplicate so we have a reference in the used module, and one in the defined module
                if not node.get_definition() in PATH_BLACKLIST:
                    new_representation[node.get_definition()][node.get_name()] = node

            if new_path not in PATH_BLACKLIST:
                new_representation[new_path][new_qualname] = node

    return new_representation
