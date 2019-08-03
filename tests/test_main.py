import unittest

from surface import bump_semantic_version, PATCH, MINOR, MAJOR


class TestSemanticBump(unittest.TestCase):
    def test_invalid(self):
        with self.assertRaises(ValueError):
            bump_semantic_version(PATCH, "12.abc.def")
        with self.assertRaises(ValueError):
            bump_semantic_version(PATCH, "34.")
        with self.assertRaises(ValueError):
            bump_semantic_version(PATCH, "12..32")
        with self.assertRaises(ValueError):
            bump_semantic_version("something", "1.2.3")

    def test_patch(self):
        self.assertEqual(bump_semantic_version(PATCH, "1.2.3"), "1.2.4")
        self.assertEqual(bump_semantic_version(PATCH, "1.2.3-alpha"), "1.2.4")
        self.assertEqual(bump_semantic_version(PATCH, "4.3.0"), "4.3.1")
        self.assertEqual(bump_semantic_version(PATCH, "2"), "2.0.1")
        self.assertEqual(bump_semantic_version(PATCH, "1.2"), "1.2.1")

    def test_minor(self):
        self.assertEqual(bump_semantic_version(MINOR, "1.2.3"), "1.3.0")
        self.assertEqual(bump_semantic_version(MINOR, "1.2.3-alpha"), "1.3.0")
        self.assertEqual(bump_semantic_version(MINOR, "4.3.0"), "4.4.0")
        self.assertEqual(bump_semantic_version(MINOR, "2"), "2.1.0")
        self.assertEqual(bump_semantic_version(MINOR, "1.2"), "1.3.0")

    def test_major(self):
        self.assertEqual(bump_semantic_version(MAJOR, "1.2.3"), "2.0.0")
        self.assertEqual(bump_semantic_version(MAJOR, "1.2.3-alpha"), "2.0.0")
        self.assertEqual(bump_semantic_version(MAJOR, "4.3.0"), "5.0.0")
        self.assertEqual(bump_semantic_version(MAJOR, "2"), "3.0.0")
        self.assertEqual(bump_semantic_version(MAJOR, "1.2"), "2.0.0")
        # Major Zero version
        self.assertEqual(bump_semantic_version(MAJOR, "0.2.3"), "0.3.0")
