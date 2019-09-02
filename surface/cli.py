""" Utilities for the cli """

if False:  # type checking
    from typing import *

import re as _re
import os as _os
import sys as _sys
import time as _time
import json as _json
import os.path as _path
import logging as _logging
import datetime as _datetime
import contextlib as _contextlib
import surface as _surface
from surface.git import Store as _Store, Git as _Git
from surface._base import PY2 as _PY2

if _PY2:
    import __builtin__ as _builtins  # type: ignore
else:
    import builtins as _builtins  # type: ignore

_WINDOWS = _os.name == "nt"


LOG = _logging.getLogger(__name__)

import_times = {}  # type: Dict[str, float]


@_contextlib.contextmanager
def time_imports():
    origin = _builtins.__import__

    def runner(name, *args, **kwargs):
        if name not in import_times:
            start = _time.time()
            LOG.debug("Importing: {}".format(name))
            module = origin(name, *args, **kwargs)
            import_times[name] = _time.time() - start
        else:
            module = origin(name, *args, **kwargs)
        return module

    _builtins.__import__ = runner
    try:
        yield
    finally:
        _builtins.__import__ = origin


def to_dict(node):  # type: (Any) -> Any
    """ Break a node structure (above types)
        into a dict representation for serialization."""
    data = {"class": type(node).__name__}  # type: Dict[str, Any]
    for key, val in node._asdict().items():
        if isinstance(
            val,
            (
                _surface.API.Var,
                _surface.API.Arg,
                _surface.API.Func,
                _surface.API.Class,
                _surface.API.Module,
                _surface.API.Unknown,
            ),
        ):
            data[key] = to_dict(val)
        elif isinstance(val, (tuple, list)):
            data[key] = [to_dict(n) for n in val]
        else:
            data[key] = val
    return data


_api_lookup = {
    "Var": _surface.API.Var,
    "Arg": _surface.API.Arg,
    "Func": _surface.API.Func,
    "Class": _surface.API.Class,
    "Module": _surface.API.Module,
    "Unknown": _surface.API.Unknown,
}


def from_dict(node):  # type: (Dict[str, Any]) -> Any
    """ Reassemble from a dict """
    # Expand everything
    node = {
        k: tuple(from_dict(n) for n in v) if isinstance(v, (tuple, list)) else v
        for k, v in node.items()
    }
    struct = _api_lookup[node.pop("class")]
    return struct(**node)


def run_dump(args):  # type: (Any) -> int
    start = _time.time()
    pythonpath = (
        _path.realpath(_path.expanduser(p.strip()))
        for p in _re.split(r"[:;]", args.pythonpath or "")
    )
    for path in pythonpath:
        _sys.path.insert(0, path)

    with time_imports():
        modules = (
            set(r for m in args.modules for r in _surface.recurse(m))
            if args.recurse
            else args.modules
        )

        module_api = []
        for module in modules:
            try:
                api = _surface.get_api(
                    module, args.exclude_modules, args.all_filter, args.depth
                )
            except ImportError as err:
                LOG.info(
                    (
                        "Failed to import '{}'.\n"
                        "{}\n"
                        "Is the module and all its dependencies in your PYTHONPATH?"
                    ).format(module, err)
                )
                return 1
            else:
                module_api.append(api)

    if not args.quiet:
        yellow = ("{}" if args.no_colour else "\033[33m{}\033[0m").format
        for mod in module_api:
            LOG.info(
                "[{}]({:.2f}s)\n".format(
                    yellow(mod.path), round(import_times.get(mod.path, 0.0), 2)
                )
            )
            LOG.info(_surface.format_api(mod.body, not args.no_colour, "    "))

    if args.output or args.git:
        serialize = {
            "meta": {
                "created": str(_datetime.datetime.now()),
                "version": _surface.__version__,
                "command": " ".join(_sys.argv[1:]),
            },
            "api": [to_dict(mod) for mod in module_api],
        }
        data = _json.dumps(serialize, indent=2, sort_keys=True)

        if args.output:
            with open(args.output, "w") as handle:
                handle.write(data)
                LOG.info("Saved API to {}".format(args.output))
        if args.git:
            path = _path.realpath(args.git)
            commit_hash = _Git().get_hash("HEAD")
            store = _Store(path)
            store.save(" ".join([">>>", "surface"] + _sys.argv[1:]), commit_hash, data)
            LOG.info(
                'Saved API as "{}", in branch "{}", to "{}"'.format(
                    commit_hash, store.BRANCH, path
                )
            )
    if not args.quiet:
        LOG.info("Took ({})".format(round(_time.time() - start, 3)))
    return 0


def run_compare(args):  # type: (Any) -> int

    if args.git:  # We are in git mode!! old / new refer to tree-ish identifiers!
        local_git = _Git()
        new_commit = local_git.get_hash(args.new)
        if args.merge:  # Use merge base as commit, instead of provided one
            old_commit = local_git.run(("merge-base", args.old, args.new))
            if not old_commit:
                raise RuntimeError("Provided branches have no commit in common.")
        else:
            old_commit = local_git.get_hash(args.old)
        repo_paths = [
            _path.realpath(path.strip())
            for path in _re.split(r"[,;]" if _WINDOWS else r"[,:]", args.git)
        ]

        old_data = new_data = None
        for repo_path in repo_paths:
            store = _Store(repo_path)
            try:
                new_data = store.load(new_commit)
            except IOError:
                pass
            try:
                old_data = store.load(old_commit)
            except IOError:
                pass
        if old_data is None or new_data is None:
            raise RuntimeError(
                "Could not find information for {} in the provided paths".format(
                    args.old if old_data is None else args.new
                )
            )
    else:
        with open(args.old, "r") as handle:
            old_data = handle.read()
        with open(args.new, "r") as handle:
            new_data = handle.read()

    old_api = sorted(
        (from_dict(mod) for mod in _json.loads(old_data)["api"]), key=lambda m: m.path
    )  # type: List[_surface.API.Module]
    new_api = sorted(
        (from_dict(mod) for mod in _json.loads(new_data)["api"]), key=lambda m: m.path
    )  # type: List[_surface.API.Module]

    purple = ("{}" if args.no_colour else "\033[35m{}\033[0m").format
    colours = {
        _surface.SemVer.PATCH: ("{}" if args.no_colour else "\033[36m{}\033[0m").format,
        _surface.SemVer.MINOR: ("{}" if args.no_colour else "\033[32m{}\033[0m").format,
        _surface.SemVer.MAJOR: ("{}" if args.no_colour else "\033[31m{}\033[0m").format,
    }

    highest_level = _surface.SemVer.PATCH
    changes = _surface.Changes().compare(old_api, new_api)
    for level, change_type, note in changes:
        LOG.info(
            "[{}] {}: {}\n".format(colours[level](level), purple(change_type), note)
        )
        if level == _surface.SemVer.MAJOR:
            highest_level = level
        elif level == _surface.SemVer.MINOR and highest_level != _surface.SemVer.MAJOR:
            highest_level = level

    if args.bump:
        _sys.stdout.write(_surface.bump_semantic_version(highest_level, args.bump))
    else:
        _sys.stdout.write(highest_level)
    if args.check and (
        args.check == highest_level or highest_level == _surface.SemVer.MAJOR
    ):
        return 1
    return 0


def run_rules(_):
    LOG.info(_surface.RULES)
    return 0


@_contextlib.contextmanager
def profile(sort):
    if not sort:
        yield
        return
    sort_columns = (
        "calls",
        "cumtime",
        "file",
        "ncalls",
        "pcalls",
        "line",
        "name",
        "nfl",
        "stdname",
        "time",
        "tottime",
    )
    if sort not in sort_columns:
        raise RuntimeError(
            "{} not a valid sort column. Please use one of {}".format(
                sort, ", ".join(sort_columns)
            )
        )
    try:
        from cProfile import Profile  # type: ignore
    except ImportError:
        from Profile import Profile  # type: ignore
    prof = Profile()
    prof.enable()
    yield
    prof.create_stats()
    prof.print_stats(sort=sort)
