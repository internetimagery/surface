""" Utilities for the cli """

if False:  # type checking
    from typing import *

import re as _re
import sys as _sys
import time as _time
import json as _json
import os.path as _path
import logging as _logging
import contextlib as _contextlib
import surface as _surface
from surface.git import Git as _Git

LOG = _logging.getLogger(__name__)


def run_dump(args):  # type: (Any) -> int
    start = _time.time()
    pythonpath = (
        _path.realpath(_path.expanduser(p.strip()))
        for p in _re.split(r"[:;]", args.pythonpath or "")
    )
    for path in pythonpath:
        _sys.path.insert(0, path)

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
            _sys.stdout.write(
                "[{}]({}s)\n".format(
                    yellow(mod.path), round(_surface.import_times.get(mod.path, 0), 2)
                )
            )
            _sys.stdout.write(_surface.format_api(mod.body, not args.no_colour, "    "))

    if args.output or args.git:
        serialize = [_surface.to_dict(mod) for mod in module_api]
        data = _json.dumps(serialize, indent=2)

        if args.output:
            with open(args.output, "w") as handle:
                handle.write(data)
                LOG.info("Saved API to {}".format(args.output))
        if args.git:
            commit = _Git.get_commit()
            path = _Git.save(commit, args.git, data)
            LOG.info("Saved API to {}".format(path))
    if not args.quiet:
        LOG.info("Took ({})".format(round(_time.time() - start, 3)))
    return 0


def run_compare(args):  # type: (Any) -> int

    if args.git:  # We are in git mode!! old / new refer to tree-ish identifiers!
        new_commit = _Git.get_commit(args.new)
        old_commit = _Git.get_merge_base(args.old, args.new)
        git_path = [path.strip() for path in _re.split(r"[,:;]", args.git)]

        new_data = _Git.load(new_commit, git_path)
        old_data = _Git.load(old_commit, git_path)
    else:
        with open(args.old, "r") as handle:
            old_data = handle.read()
        with open(args.new, "r") as handle:
            new_data = handle.read()

    old_api = sorted(
        (_surface.from_dict(mod) for mod in _json.loads(old_data)), key=lambda m: m.path
    )  # type: List[_surface.Module]
    new_api = sorted(
        (_surface.from_dict(mod) for mod in _json.loads(new_data)), key=lambda m: m.path
    )  # type: List[_surface.Module]

    purple = ("{}" if args.no_colour else "\033[35m{}\033[0m").format
    colours = {
        _surface.PATCH: ("{}" if args.no_colour else "\033[36m{}\033[0m").format,
        _surface.MINOR: ("{}" if args.no_colour else "\033[32m{}\033[0m").format,
        _surface.MAJOR: ("{}" if args.no_colour else "\033[31m{}\033[0m").format,
    }

    highest_level = _surface.PATCH
    changes = _surface.compare(old_api, new_api)
    for level, change_type, note in changes:
        if not args.quiet:
            LOG.info(
                "[{}] {}: {}".format(colours[level](level), purple(change_type), note)
            )
        if level == _surface.MAJOR:
            highest_level = level
        elif level == _surface.MINOR and highest_level != _surface.MAJOR:
            highest_level = level

    if args.bump:
        _sys.stdout.write(_surface.bump_semantic_version(highest_level, args.bump))
    else:
        _sys.stdout.write(highest_level)
    if args.check and (args.check == highest_level or highest_level == _surface.MAJOR):
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
