""" Git utility, for cli """

if False:  # type checking
    from typing import *

import re as _re
import os as _os
import datetime as _datetime
import subprocess as _subprocess
import collections as _collections


class Store(object):

    BRANCH = "surface_API_store"

    _hash_break = 3

    def __init__(self, root):
        self._repo = Repo(root)

    def save(self, message, hash, data):
        """ Save data under corresponding hash """
        root_hash = hash[: self._hash_break]
        base_hash = hash[self._hash_break:]
        # Get our root
        branch = self._repo.get_branch(self.BRANCH)
        root_tree = branch.get_tree()
        # Store our data
        base_tree = root_tree.get(root_hash)
        if base_tree is None:
            base_tree = self._repo.new_tree()
        blob = self._repo.new_blob(data)
        blob.save()
        base_tree = base_tree.set(base_hash, blob)
        base_tree.save()
        root_tree = root_tree.set(root_hash, base_tree)
        root_tree.save()
        # Lock it in with a commit
        branch.commit(root_tree, message)

    def load(self, hash):
        """ Load data under corresponding hash """
        root_hash = hash[: self._hash_break]
        base_hash = hash[self._hash_break:]
        # Get our root
        branch = self._repo.get_branch(self.BRANCH)
        root_tree = branch.get_tree()
        # Load our data
        base_tree = root_tree.get(root_hash)
        if base_tree is None:
            raise IOError("Hash cannot be found {}".format(hash))
        blob = base_tree.get(base_hash)
        if blob is None:
            raise IOError("Hash cannot be found {}".format(hash))
        return blob.data

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

    def run_raw(self, *args, input=None):
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
            raise self.FatalError(output[1].decode("utf-8").strip())
        return output[0]

    def run(self, *args, **kwargs):
        return self.run_raw(*args, **kwargs).decode("utf-8").strip()


class Base(object):
    def __new__(cls, git, data, hash=None):
        obj = object.__new__(cls)
        object.__setattr__(obj, "_git", git)
        object.__setattr__(obj, "_data", data)
        object.__setattr__(obj, "_hash", hash)
        return obj

    @property
    def hash(self):
        if self._hash is None:
            raise RuntimeError("Object {} not saved.".format(self))
        return self._hash

    @property
    def data(self):
        return self._data

    def save(self):
        raise RuntimeError("Object cannot be saved.")


class Blob(Base):
    @classmethod
    def from_hash(cls, git, hash):
        data = git.run_raw("cat-file", "blob", hash)
        return cls(git, data, hash)

    def save(self):
        self._hash = self._git.run("hash-object", "-w", "--stdin", input=self.data)


class Tree(Base):

    _entry = _collections.namedtuple("_entry", ("mod", "type", "hash"))
    _entry_reg = _re.compile(r"^(\d{6}) ([a-z]+) ([a-f0-9]{40})\s+(.+)$", _re.M)
    _entry_template = "{mod} {type} {hash}\t{name}"

    @classmethod
    def from_hash(cls, git, hash):
        data = git.run("cat-file", "-p", hash)
        entries = {
            match.group(4).strip(): cls._entry(
                mod=match.group(1), type=match.group(2), hash=match.group(3)
            )
            for match in cls._entry_reg.finditer(data)
        }
        return cls(git, entries, hash)

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
        try:
            entry = self._data[name]
        except KeyError:
            return default
        if entry.type == "tree":
            return Tree.from_hash(self._git, entry.hash)
        elif entry.type == "blob":
            return Blob.from_hash(self._git, entry.hash)
        else:
            raise TypeError("Unhandled type {}".format(entry.type))

    def save(self):
        data = "\n".join(
            self._entry_template.format(
                mod=entry.mod, type=entry.type, hash=entry.hash, name=name
            )
            for name, entry in self.data.items()
        )
        self._hash = self._git.run("mktree", input=data.encode("utf-8"))


class Branch(object):
    def __init__(self, git, name):
        self._git = git
        self._name = name

    def get_tree(self):
        try:
            latest_tree = self._git.run("rev-parse", "{}^{{tree}}".format(self._name))
        except self._git.FatalError:
            # Branch does not exist. Create empty tree.
            return Tree(self._git, {})
        else:
            return Tree.from_hash(self._git, latest_tree)

    def commit(self, tree, message):
        try:
            # Get latest commit
            parent = self._git.run("rev-parse", "{}^{{commit}}".format(self._name))
        except self._git.FatalError:
            # No commit made yet. Branch is likely new
            new_commit = self._git.run(
                "commit-tree", tree.hash, input=message.encode("utf-8")
            )
        else:
            new_commit = self._git.run(
                "commit-tree", tree.hash, "-p", parent, input=message.encode("utf-8")
            )
        self._git.run("update-ref", "refs/heads/{}".format(self._name), new_commit)


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
