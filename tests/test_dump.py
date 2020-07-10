import os.path
import unittest
import shutil
import tempfile
import filecmp

from pyhike import TrailBlazer

from surface.dump import Exporter

TESTDATA = os.path.join(os.path.dirname(__file__), "testdata")
SOURCES = os.path.join(TESTDATA, "sources")
EXPECT = os.path.join(TESTDATA, "expect")


class TestExportStubs(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tempdir = tempfile.mkdtemp("TEST")

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _test_file(self, name):
        source_path = os.path.join(SOURCES, name)
        expect_path = os.path.join(EXPECT, name)
        Exporter(directories=[source_path]).export(self.tempdir)

        results = filecmp.dircmp(expect_path, self.tempdir)
        for filename in results.diff_files:
            with open(os.path.join(expect_path, filename)) as fh1:
                with open(os.path.join(self.tempdir, filename)) as fh2:
                    self.assertEqual(fh1.read(), fh2.read())

        # test_path = os.path.join(self.tempdir, name + "i")
        # expect_path = os.path.join(EXPECT, name + "i")
        # with open(test_path) as fh1:
        #    with open(expect_path) as fh2:
        #        self.assertEqual(fh1.read(), fh2.read())

    def test_simple(self):
        self._test_file("simple")


if __name__ == "__main__":
    unittest.main()
