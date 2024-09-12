import unittest

from objutils.utils import cygpath_to_win


class TestCygpath(unittest.TestCase):
    def test01(self):
        self.assertEqual(
            cygpath_to_win("/cygdrive/c/projects/foobar/flonz"),
            r"c:\projects\foobar\flonz",
        )

    def test02(self):
        self.assertEqual(cygpath_to_win(r"c:\projects\foobar\flonz"), r"c:\projects\foobar\flonz")


def main():
    unittest.main()


if __name__ == "__main__":
    main()
