import os.path
import unittest
import shutil
import tempfile

from pyhike import TrailBlazer

from surface.dump import Exporter

TESTDATA = os.path.join(os.path.dirname(__file__), "testdata")


class TestExportStubs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp(
            "TEST", dir=os.path.join(os.path.dirname(__file__), "EXPORT")
        )
        # cls.tempdir = tempfile.mkdtemp("TEST")
        Exporter(directories=[TESTDATA]).export(cls.tempdir)

    # @classmethod
    # def tearDownClass(cls):
    #    shutil.rmtree(cls.tempdir)

    def test_stub_structure(self):
        with open(os.path.join(self.tempdir, "test_mod_basic", "myModule.pyi")) as fh:
            print("CONTENT")
            print(fh.read())
