import os.path
import unittest
import shutil
import tempfile

from pyhike import TrailBlazer

from surface.dump import RepresentationBuilder, export_stubs

TESTDATA = os.path.join(os.path.dirname(__file__), "testdata")

class TestExportStubs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp("TEST")
        visitor = RepresentationBuilder()
        TrailBlazer(visitor).roam_directory(TESTDATA).hike()
        export_stubs(visitor.get_representation(), cls.tempdir)
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)
    
    def test_stub_structure(self):
        with open(os.path.join(self.tempdir, "test_comments.pyi")) as fh:
            print("CONTENT")
            print(fh.read())
