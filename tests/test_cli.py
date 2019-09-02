import subprocess
import unittest
import tempfile
import shutil
import stat
import os

from surface import bump_semantic_version, SemVer


class TestRun(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp, onerror=self.remove_protected)

    def remove_protected(self, action, name, exc):
        os.chmod(name, stat.S_IWRITE)
        os.remove(name)

    def test_dump(self):
        command = ["surface", "-q", "dump", "--depth", "1", "surface"]
        subprocess.check_call(command)

    def test_dump_output(self):
        output = os.path.join(self.temp, "myfile.json")
        command = ["surface", "-q", "dump", "--depth", "1", "-o", output, "surface"]
        subprocess.check_call(command)

    def test_dump_git(self):
        command = [
            "surface",
            "-q",
            "dump",
            "--depth",
            "1",
            "--git",
            self.temp,
            "surface",
        ]
        subprocess.check_call(command)

    def test_compare_output(self):
        output = os.path.join(self.temp, "myfile.json")
        command = ["surface", "-q", "dump", "--depth", "1", "-o", output, "surface"]
        subprocess.check_call(command)
        command = ["surface", "-q", "compare", output, output]
        subprocess.check_call(command)

    def test_compare_git(self):
        command = [
            "surface",
            "-q",
            "dump",
            "--depth",
            "1",
            "--git",
            self.temp,
            "surface",
        ]
        subprocess.check_call(command)
        command = [
            "surface",
            "--pdb",
            "-q",
            "compare",
            "--git",
            self.temp,
            "HEAD",
            "HEAD",
        ]
        print(self.temp, os.getcwd())
        subprocess.check_call(command)


if __name__ == "__main__":
    unittest.main()
