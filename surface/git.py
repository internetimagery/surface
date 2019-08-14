""" Git utility, for cli """

if False:  # type checking
    from typing import *

import os as _os
import gzip as _gzip
import errno as _errno
import subprocess as _subprocess

__all__ = ("GitError", "Git")


class GitError(Exception):
    pass


class Git(object):
    """ Git helper to get commits """

    # --------------------------------------
    # Get commits out of git
    # --------------------------------------

    @classmethod
    def get_commit(cls, treeish="HEAD"):  # type: (str) -> str
        """ Convert provded name into concrete commit hash """
        command = ["git", "rev-parse", "--verify", treeish]
        commit = cls._run(command).strip()
        return commit

    @classmethod
    def get_merge_base(cls, branch1, branch2="HEAD"):  # type: (str, str) -> str
        """ Get commit that will be used as a base if these two branches were merged """
        command = ["git", "merge-base", branch1, branch2]
        commit = cls._run(command).strip()
        return commit

    # --------------------------------------
    # Store data inside directory
    # --------------------------------------

    @classmethod
    def save(cls, commit, storage_directory, data):  # type: (str, str, str) -> str
        """ Save data to location """
        storage_directory = _os.path.realpath(storage_directory)
        if not _os.path.isdir(storage_directory):
            raise GitError("Path is not a directory: {}".format(storage_directory))

        sub_dir, leaf = cls._format_commit(commit)
        storage_sub_dir = _os.path.join(storage_directory, sub_dir)
        storage_path = _os.path.join(storage_sub_dir, leaf)
        try:
            _os.mkdir(storage_sub_dir)
        except OSError as err:
            if err.errno != _errno.EEXIST:
                raise
        with _gzip.open(storage_path, "w") as handle:
            handle.write(data.encode("utf-8"))
        return storage_path

    @classmethod
    def load(cls, commit, storage_directories):  # type: (str, Sequence[str]) -> Any
        """ Look for, and load the provided commit, in any of the provided directories """
        parts = cls._format_commit(commit)
        for storage_dir in storage_directories:
            storage_path = _os.path.join(storage_dir, *parts)
            try:
                with _gzip.open(storage_path) as handle:
                    return handle.read()
            except IOError as err:
                if err.errno != _errno.ENOENT:
                    raise
        raise GitError("Cannot find the commit {}".format(commit))

    # --------------------------------------
    # Helpers
    # --------------------------------------

    @staticmethod
    def _format_commit(commit):
        return commit[:2], "{}.json.gz".format(commit[2:])

    @staticmethod
    def _run(command):
        try:
            output = _subprocess.check_output(command, stderr=_subprocess.STDOUT)
        except _subprocess.CalledProcessError as err:
            raise GitError("Git {}".format(err.output.decode("utf-8")))
        except OSError as err:
            raise GitError("Could not find git. Is it correctly installed?")
        else:
            return output.decode("utf-8")


if __name__ == "__main__":
    print(Git.save("abcdefghijklmnopqrstuvwxyz", "./", "hello there"))
    print(Git.load("abcdefghijklmnopqrstuvwxyzz", "./"))
