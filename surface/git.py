""" Git utility, for cli """

if False:  # type checking
    from typing import *

import re as _re
import os as _os
import gzip as _gzip
import errno as _errno
import datetime as _datetime
import subprocess as _subprocess
import collections as _collections

__all__ = ("GitError", "Git")


class Store(object):

    BRANCH = "surface_API_store"

    _base_dir_len = 3

    def __init__(self, root):
        self._repo = Repo(root)

    def save(self, hash, data):
        """ Save data under corresponding hash """
        base_dir = hash[: self._base_dir_len]

        # Get our root
        branch = self._repo.get_branch(self.BRANCH)
        root_tree = branch.get_tree()
        # Store our data
        base_tree = root_tree.get(base_dir)
        if base_tree is None:
            base_tree = self._repo.new_tree()
        blob = self._repo.new_blob(data)
        blob.save()
        base_tree = base_tree.set(hash, blob)
        base_tree.save()
        root_tree = root_tree.set(base_dir, base_tree)
        root_tree.save()
        branch.commit(root_tree, "Added at {}".format(_datetime.datetime.now()))

    def load(self, hash):
        """ Load data under corresponding hash """
        pass

    def _get_tree(self):
        hash = self._git.get_hash("{}^{{tree}}".format(self.BRANCH))
        return hash


class Git(object):
    """ Run git commands """

    class FatalError(Exception):
        pass

    EXEC = "git"

    def __init__(self, root):
        self._root = root

    def get_hash(self, identifier):
        return self.run("rev-parse", "--verify", identifier)

    def run(self, *args, input=None):
        try:
            proc = _subprocess.Popen(
                (self.EXEC,) + args,
                stdin=_subprocess.PIPE,
                stdout=_subprocess.PIPE,
                stderr=_subprocess.PIPE,
                cwd=self._root,
            )
            output = proc.communicate(input)
        except OSError:
            raise RuntimeError("Could not find git. Is it correctly installed?")
        if proc.returncode:
            raise self.FatalError(output[1].decode("utf-8"))
        return output[0]


class Base(object):
    def __new__(cls, git, data, hash=None):
        obj = object.__new__(cls)
        object.__setattr__(obj, "_git", git)
        object.__setattr__(obj, "_data", data)
        object.__setattr__(obj, "_hash", hash)
        return obj

    @classmethod
    def from_hash(cls, git, hash):
        cmd = ["git", "cat-file", "-p", hash]
        data = self._run(cmd)
        return cls(git, data, hash)

    @property
    def hash(self):
        if self._hash is None:
            raise RuntimeError("Object {} not saved.".format(self))
        return self._hash

    def save(self):
        raise RuntimeError("Object cannot be saved.")


class Blob(Base):
    def save(self):
        self._hash = (
            self._git.run("hash-object", "-w", "--stdin", input=self._data)
            .decode("utf-8")
            .strip()
        )


class Tree(Base):

    _entry = _collections.namedtuple("_entry", ("mod", "type", "hash"))
    _entry_reg = _re.compile(r"^(\d{6}) [a-z]+ ([a-f0-9]{40})\s+(.+)$", _re.M)
    _entry_template = "{mod} {type} {hash}\t{name}"

    def set(self, name, item):
        """ Add / Edit an object of name """
        if isinstance(item, Tree):
            entry = self._entry("040000", "tree", item.hash)
        elif isinstance(item, Blob):
            entry = self._entry("100644", "blob", item.hash)
        else:
            raise TypeError("Bad type {}".format(type(item)))
        entries = self._data.copy()
        entries[name] = entry
        return self.__class__(self._git, entries, hash=None)

    def get(self, name, default=None):
        """ Get item from within. """
        return self._data.get(name, default)

    def save(self):
        data = "\n".join(
            self._entry_template.format(
                mod=entry.mod, type=entry.type, hash=entry.hash, name=name
            )
            for name, entry in self._data.items()
        )
        self._hash = (
            self._git.run("mktree", input=data.encode("utf-8")).decode("utf-8").strip()
        )


class Commit(Base):
    def save(self, message=""):
        # TODO: commit needs a parent, and tree id
        cmd = ["git", "commit-tree", treeID, "-p", parentID]
        self._hash = self._run(cmd, input=message)


class Branch(object):
    def __init__(self, git, name):
        self._git = git
        self._name = name

    def get_tree(self):
        try:
            # Get tree attached to latest commit on branch.
            hash = self._git.run("rev-parse", "{}^{{tree}}".format(self._name))
            return Tree.from_hash(self._git, hash)
        except self._git.FatalError:
            # Branch does not exist. Create empty tree.
            return Tree(self._git, {})

    def commit(self, tree, message):
        try:
            # Get latest commit
            parent = self._git.run("rev-parse", "{}^{{commit}}".format(self._name)).decode("utf-8").strip()
        except self._git.FatalError:
            # No commit made yet. Branch is likely new
            self._git.run("commit-tree", tree.hash)
        else:
            self._git.run("commit-tree", tree.hash, "-p", parent)


class Repo(object):
    def __init__(self, root, bare=True):
        root = _os.path.realpath(root)
        if not _os.path.isdir(root):
            raise IOError("Directory does not exist: {}".format(root))
        self._git = Git(root)
        try:
            # Get actual repo root
            self._root = self._git.run("rev-parse", "--show-toplevel")
        except self._git.FatalError:
            # Make repo
            if bare:
                self._git.run("init", "--bare")
            else:
                self._git.run("init")
            self._root = root

    def get_branch(self, name):
        return Branch(self._git, name)

    def new_tree(self):
        return Tree(self._git, {})

    def new_blob(self, data):
        return Blob(self._git, data)


# class GitError(Exception):
#     pass


# class Git(object):
#     """ Git helper to get commits """
#
#     # --------------------------------------
#     # Get commits out of git
#     # --------------------------------------
#
#     @classmethod
#     def get_commit(cls, treeish="HEAD"):  # type: (str) -> str
#         """ Convert provded name into concrete commit hash """
#         command = ["git", "rev-parse", "--verify", treeish]
#         commit = cls._run(command).strip()
#         return commit
#
#     @classmethod
#     def get_merge_base(cls, branch1, branch2="HEAD"):  # type: (str, str) -> str
#         """ Get commit that will be used as a base if these two branches were merged """
#         command = ["git", "merge-base", branch1, branch2]
#         commit = cls._run(command).strip()
#         return commit
#
#     # --------------------------------------
#     # Store data inside directory
#     # --------------------------------------
#
#     @classmethod
#     def save(cls, commit, storage_directory, data):  # type: (str, str, str) -> str
#         """ Save data to location """
#         storage_directory = _os.path.realpath(storage_directory)
#         if not _os.path.isdir(storage_directory):
#             raise GitError("Path is not a directory: {}".format(storage_directory))
#
#         sub_dir, leaf = cls._format_commit(commit)
#         storage_sub_dir = _os.path.join(storage_directory, sub_dir)
#         storage_path = _os.path.join(storage_sub_dir, leaf)
#         try:
#             _os.mkdir(storage_sub_dir)
#         except OSError as err:
#             if err.errno != _errno.EEXIST:
#                 raise
#         with _gzip.open(storage_path, "w") as handle:
#             handle.write(data.encode("utf-8"))
#         return storage_path
#
#     @classmethod
#     def load(cls, commit, storage_directories):  # type: (str, Sequence[str]) -> Any
#         """ Look for, and load the provided commit, in any of the provided directories """
#         parts = cls._format_commit(commit)
#         for storage_dir in storage_directories:
#             storage_path = _os.path.join(storage_dir, *parts)
#             try:
#                 with _gzip.open(storage_path) as handle:
#                     return handle.read()
#             except IOError as err:
#                 if err.errno != _errno.ENOENT:
#                     raise
#         raise GitError("Cannot find the commit {}".format(commit))
#
#     # --------------------------------------
#     # Helpers
#     # --------------------------------------
#
#     @staticmethod
#     def _format_commit(commit):
#         return commit[:2], "{}.json.gz".format(commit[2:])
#
#     @staticmethod
#     def _run(command):
#         try:
#             output = _subprocess.check_output(command, stderr=_subprocess.STDOUT)
#         except _subprocess.CalledProcessError as err:
#             raise GitError("Git {}".format(err.output.decode("utf-8")))
#         except OSError as err:
#             raise GitError("Could not find git. Is it correctly installed?")
#         else:
#             return output.decode("utf-8")


if __name__ == "__main__":
    print(Git.save("abcdefghijklmnopqrstuvwxyz", "./", "hello there"))
    print(Git.load("abcdefghijklmnopqrstuvwxyzz", "./"))
