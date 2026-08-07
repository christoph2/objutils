import unittest
import io
from objutils import probes, registry

# Test Data
IHEX = b":100000004578616D706C65207769746820616E2039\n:00000001FF\n"
SREC = b"S113B000576F77212044696420796F7520726561D8\nS9030000FC\n"
ASH = b"\x02 $A0000,\nFF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF\n\x03$$0FF0,\n"
TITEXT = b"@DEAD\n99 F2 B9 CB 79 D3 EE F8 8F C6 A9 40 AB CD 71 A6\nq\n"
TEK = b"/B000100C576F77212044696420796F7520726561A5\n/B03D001B\n"
MOSTEC = b";10B000576F77212044696420796F75207265610624\n;00\n"
# Signetics: :AAAALLBBDDCC. AAAA=1000, LL=10 (16), BB=checksum.
# addr_bytes = [0x10, 0x00], len = 16. rotatedXOR([0x10, 0x00, 16])
# 0x10 << 1 = 0x20. 0x20 ^ 0x00 = 0x20. 0x20 << 1 = 0x40. 0x40 ^ 16 (0x10) = 0x50.
SIG = b":100010504578616D706C65207769746820616E2039\n:101000\n"
EMON52 = b"10 0000:57 6F 77 21 20 44 69 64 20 79 6F 75 20 72 65 61 0564\n"
# FPC: base85 encoded.
FPC = b"fpc:1.0\n>0000:8p&Yj8p&Yj8p&Yj8p&Yj\n"
# RCA format
RCA = b"\x00" * 48 + b"\r\n!M\n1000 12 34 56 78;\n"

FORMATS = {
    "ihex": IHEX,
    "srec": SREC,
    "ash": ASH,
    "titxt": TITEXT,
    "tek": TEK,
    "mostec": MOSTEC,
    "sig": SIG,
    "emon52": EMON52,
    "fpc": FPC,
    "rca": RCA,
}


class TestProbeUniqueness(unittest.TestCase):
    def test_all_probes(self):
        for name, data in FORMATS.items():
            with self.subTest(format=name):
                detected = probes(data)
                self.assertEqual(detected, name, f"Expected {name}, but detected {detected}")

    def test_cross_probing(self):
        # For each format's data, check if other formats' readers incorrectly accept it.
        all_formats = registry.formats

        for name, data in FORMATS.items():
            for reader_name in all_formats:
                if reader_name == name:
                    continue

                # Some readers might not have a specialized probe() and fall back to regex match.
                # We want to see if any OTHER reader fälschlicherweise returns True.
                codec = registry.get(reader_name)
                reader = codec.Reader()

                with self.subTest(data_format=name, reader=reader_name):
                    res = reader.probe(io.BytesIO(data))
                    # It's okay if multiple readers return True IF the global probes() handles priority correctly,
                    # but ideally probe() should be as specific as possible.
                    # Especially for ihex vs sig vs mostec.
                    if name == "ihex" and reader_name in ["sig", "mostec"]:
                        self.assertFalse(res, f"Reader {reader_name} should NOT accept {name} data")
                    if name == "sig" and reader_name in ["ihex", "mostec"]:
                        self.assertFalse(res, f"Reader {reader_name} should NOT accept {name} data")
                    if name == "mostec" and reader_name in ["ihex", "sig"]:
                        self.assertFalse(res, f"Reader {reader_name} should NOT accept {name} data")


if __name__ == "__main__":
    unittest.main()
