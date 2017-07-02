import unittest


import xorgauth


class BaseTests(unittest.TestCase):
    def test_version(self):
        self.assertIsNotNone(xorgauth.__version__)
