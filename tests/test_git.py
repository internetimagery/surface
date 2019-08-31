import stat
import shutil
import os.path
import unittest
import tempfile

from surface.git import Store


class TestGit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp, onerror=self.remove_protected)

    def remove_protected(self, action, name, exc):
        os.chmod(name, stat.S_IWRITE)
        os.remove(name)

    def test_store_new(self):
        data = "ABCD".encode("ascii")
        hash = "a30a285157af49e1e4555ceec0ad341c1b0fc6e0"
        store = Store(self.temp)
        store.save("mymessage", hash, data)
        self.assertEqual(data, store.load(hash))

    def test_load_empty(self):
        hash = "a30a285157af49e1e4555ceec0ad341c1b0fc6e0"
        store = Store(self.temp)
        with self.assertRaises(IOError):
            store.load(hash)


if __name__ == "__main__":
    unittest.main()
