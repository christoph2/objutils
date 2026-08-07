import unittest
import os
import tempfile
from objutils import Section, Image, LazySection, InvalidAddressError


class TestExtendedFeatures(unittest.TestCase):
    def test_lazy_section(self):
        # Create a dummy file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Hello World, this is a test for LazySection.")
            filename = f.name

        try:
            ls = LazySection(0x1000, filename)
            self.assertEqual(ls.start_address, 0x1000)
            self.assertEqual(ls.length, 44)
            self.assertEqual(bytes(ls.data[:5]), b"Hello")

            # Check read-only
            with self.assertRaises(NotImplementedError):
                ls.write(0x1000, b"Fail")

            ls.__del__()  # Close file/mmap
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    def test_address_validation(self):
        s1 = Section(0x1000, b"\x00" * 0x100, name="S1")
        s2 = Section(0x2000, b"\x00" * 0x100, name="S2")
        img = Image([s1, s2])

        # Valid change
        s1.start_address = 0x1500
        self.assertEqual(s1.start_address, 0x1500)

        # Invalid change (overlap with s2)
        with self.assertRaises(InvalidAddressError):
            s1.start_address = 0x1F50  # 0x1F50 + 0x100 = 0x2050 -> Overlaps with 0x2000

        # Address alias
        s2.address = 0x3000
        self.assertEqual(s2.start_address, 0x3000)

    def test_dumps_return_type(self):
        from objutils import dumps

        s = Section(0, b"data")
        img = Image([s])
        res = dumps("srec", img)
        self.assertIsInstance(res, bytearray)


if __name__ == "__main__":
    unittest.main()
