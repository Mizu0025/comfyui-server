import os
import unittest
from filename_utils import get_domain_path

class TestFilenameUtils(unittest.TestCase):
    def test_get_domain_path_with_domain(self):
        filepath = "/home/mizu/Pictures/artbot/12345_abc_1.webp"
        domain = "https://fate.bot"
        expected = "https://fate.bot/12345_abc_1.webp"
        self.assertEqual(get_domain_path(filepath, domain), expected)

    def test_get_domain_path_with_domain_trailing_slash(self):
        filepath = "/home/mizu/Pictures/artbot/12345_abc_1.webp"
        domain = "https://fate.bot/"
        expected = "https://fate.bot/12345_abc_1.webp"
        self.assertEqual(get_domain_path(filepath, domain), expected)

    def test_get_domain_path_without_domain(self):
        filepath = "/home/mizu/Pictures/artbot/12345_abc_1.webp"
        domain = ""
        expected = "12345_abc_1.webp"
        self.assertEqual(get_domain_path(filepath, domain), expected)

    def test_get_domain_path_empty_path(self):
        self.assertEqual(get_domain_path("", "https://fate.bot"), "")
        self.assertEqual(get_domain_path(None, "https://fate.bot"), "")

if __name__ == "__main__":
    unittest.main()
