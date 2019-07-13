
import sys
import os.path
import unittest

from importlib import reload

from surface._traversal import traverse

path = os.path.join(os.path.dirname(__file__), "testdata")
sys.path.insert(0, path)
import test_mod_basic

class TestImporter(unittest.TestCase):

    def setUp(self):
        reload(test_mod_basic)

    def test_basic(self):
        data = list(traverse(test_mod_basic))
        import pprint
        pprint.pprint(data)

if __name__ == '__main__':
    unittest.main()
