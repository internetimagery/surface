import imp
import sys
import os.path
import unittest

from surface._base import *
from surface._compare import *
from surface._traversal import Traversal

root = os.path.join(os.path.dirname(__file__), "testdata", "test_mod_compare")


class TestCompare(unittest.TestCase):
    @staticmethod
    def get_module(name, rename=""):
        mod_name = rename or name
        module = imp.load_source(mod_name, os.path.join(root, "{}.py".format(name)))
        api = [Traversal().traverse(module)]
        del sys.modules[mod_name]
        return api

    def test_no_change(self):
        patchA = self.get_module("patchA")
        changes = Changes().compare(patchA, patchA)
        self.assertEqual(changes, set())

        publicA = self.get_module("publicA")
        publicB = self.get_module("publicB", "publicA")
        changes = Changes().compare(publicA, publicB)
        self.assertEqual(changes, set())

    def test_patch(self):
        patchA = self.get_module("patchA")
        patchB = self.get_module("patchB", "patchA")
        changes = Changes().compare(patchA, patchB)
        # fmt: off
        self.assertEqual(
            changes,
            set([
                Change('patch', 'Renamed API.Arg', 'patchA.rename_args_var(b), Was: "a", Now: "b"'),
                Change('patch', 'Renamed API.Arg', 'patchA.rename_kwargs_var(b), Was: "a", Now: "b"'),
                Change('patch', 'Renamed API.Arg', 'patchA.MethRenameVar.rename_meth_args_var(b), Was: "a", Now: "b"'),
                Change('patch', 'Renamed API.Arg', 'patchA.MethRenameVar.rename_meth_kwargs_var(b), Was: "a", Now: "b"'),
                Change('patch', 'Type Changed', 'patchA.add_new_types(a), Was: "~unknown", Now: "str"'),
                Change('patch', 'Type Changed', 'patchA.add_new_types(b), Was: "typing.Optional[~unknown]", Now: "typing.Optional[str]"'),
                Change('patch', 'Return Type Changed', 'patchA.add_new_types, Was: "~unknown", Now: "None"'),
            ]),
        )
        # fmt: on

    def test_minor(self):
        minorA = self.get_module("minorA")
        minorB = self.get_module("minorB", "minorA")
        changes = Changes().compare(minorA, minorB)
        # fmt: off
        self.assertEqual(
            changes,
            set([
                Change('minor', 'Added', 'minorA.new_var'),
                Change('minor', 'Added', 'minorA.new_func'),
                Change('minor', 'Added', 'minorA.NewClass'),
                Change('minor', 'Added', 'minorA.NewMeth.new_method'),
                Change('minor', 'Added API.Arg', 'minorA.new_kwarg_opt(b)'),
                Change('minor', 'Added API.Arg', 'minorA.new_arg_var(b)'),
                Change('minor', 'Added API.Arg', 'minorA.new_kwarg_var(b)'),
                Change('minor', 'Kind Changed', 'minorA.change_arg_opt(a)'),
                Change('minor', 'Added API.Arg', 'minorA.NewMethArgs.new_meth_kwarg_opt(b)'),
                Change('minor', 'Added API.Arg', 'minorA.NewMethArgs.new_meth_arg_var(b)'),
                Change('minor', 'Added API.Arg', 'minorA.NewMethArgs.new_meth_kwarg_var(b)'),
                Change('minor', 'Kind Changed', 'minorA.NewMethArgs.change_meth_arg_opt(a)'),
                Change('minor', 'Type Changed', 'minorA.type_changed(a), Was: "typing.Dict[str, str]", Now: "typing.Mapping[str, str]"'),
                Change('minor', 'Could not verify', 'minorA.UnknownChange.ohno: ERROR'),
            ]),
        )
        # fmt: on
        minorC = self.get_module("minorC")
        minorD = self.get_module("minorD", "minorC")
        changes = Changes().compare(minorC, minorD)
        self.assertEqual(changes, set([Change("minor", "Added", "minorC.something")]))
        changes = Changes().compare([], minorC)
        self.assertEqual(changes, set([Change("minor", "Added", "minorC")]))

    def test_major(self):
        majorA = self.get_module("majorA")
        majorB = self.get_module("majorB", "majorA")
        changes = Changes().compare(majorA, majorB)
        # fmt: off
        self.assertEqual(
            changes,
            set([
                Change("major", "Renamed API.Arg", 'majorA.arg_rename(b), Was: "a", Now: "b"'),
                Change("major", "Renamed API.Arg", 'majorA.opt_arg_rename(c), Was: "b", Now: "c"'),
                Change('major', 'Added API.Arg', 'majorA.arg_new(b)'),
                Change('major', 'Removed API.Arg', 'majorA.arg_gone(b)'),
                Change('major', 'Removed API.Arg', 'majorA.opt_arg_gone(b)'),
                Change('major', 'Removed API.Arg', 'majorA.var_arg_gone(b)'),
                Change("major", "Removed", "majorA.func_gone"),
                Change("major", "Removed", "majorA.ClassGone"),
                Change('major', 'Removed', 'majorA.MethGone.method_gone'),
                Change("major", "Removed", "majorA.var_gone"),
                Change("major", "Type Changed", 'majorA.type_change, Was: "str", Now: "int"'),
                Change('major', 'Type Changed', 'majorA.arg_type_change(a), Was: "int", Now: "bool"'),
                Change('major', 'Type Changed', 'majorA.arg_type_change(b), Was: "str", Now: "int"'),
                Change('major', 'Type Changed', 'majorA.arg_type_change(c), Was: "bool", Now: "str"'),
                Change('major', 'Return Type Changed', 'majorA.arg_type_change, Was: "int", Now: "bool"'),
                Change('major', 'Return Type Changed', 'majorA.return_type_change_subtype, Was: "typing.List[str]", Now: "typing.Sequence[str]"'),
                Change('major', 'Type Changed', 'majorA.MethTypeChange.meth_type_change(a), Was: "int", Now: "bool"'),
                Change('major', 'Type Changed', 'majorA.MethTypeChange.meth_type_change(b), Was: "str", Now: "int"'),
                Change('major', 'Type Changed', 'majorA.MethTypeChange.meth_type_change(c), Was: "bool", Now: "str"'),
                Change('major', 'Return Type Changed', 'majorA.MethTypeChange.meth_type_change, Was: "int", Now: "bool"'),

            ]),
        )
        # fmt: on
        majorC = self.get_module("majorC")
        majorD = self.get_module("majorD", "majorC")
        changes = Changes().compare(majorC, majorD)
        self.assertEqual(changes, set([Change("major", "Removed", "majorC.var_gone")]))
        changes = Changes().compare(majorD, [])
        self.assertEqual(changes, set([Change("major", "Removed", "majorC")]))


if __name__ == "__main__":
    unittest.main()
