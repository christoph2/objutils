import pytest

from objutils.checksums import (
    COMPLEMENT_NONE,
    COMPLEMENT_ONES,
    COMPLEMENT_TWOS,
    ROTATE_LEFT,
    ROTATE_RIGHT,
    check,
    lrc,
    nibble_sum,
    rotatedXOR,
    xor,
)


def testNibbleSumCase1():
    assert nibble_sum(range(10)) == 45


def testNibbleSumCase2():
    assert nibble_sum(range(100)) == 222

    # check that s.split fails when the separator is not a string
    # with self.assertRaises(TypeError):
    #    s.split(2)


def testXorInverted():
    assert xor([0xBC, 0xAF, 0xFE, 0x11, 0x52, 0x60, 0x80], True) == 0xB1


def testXorNotInverted():
    assert xor([0xBC, 0xAF, 0xFE, 0x11, 0x52, 0x60, 0x80], False) == 0x4E


def testLRCCase1():
    assert lrc(range(10), 8, COMPLEMENT_NONE) == 45


def testLRCCase2():
    assert lrc(range(100), 8, COMPLEMENT_NONE) == 86


def testLRCCase3():
    assert lrc(range(10), 8, COMPLEMENT_ONES) == 210


def testLRCCase4():
    assert lrc(range(100), 8, COMPLEMENT_ONES) == 169


def testLRCCase5():
    assert lrc(range(10), 8, COMPLEMENT_TWOS) == 211


def testLRCCase6():
    assert lrc(range(100), 8, COMPLEMENT_TWOS) == 170


def testLRCCase7():
    assert lrc(range(10), 16, COMPLEMENT_NONE) == 45


def testLRCCase8():
    assert lrc(range(100), 16, COMPLEMENT_NONE) == 4950


def testLRCCase9():
    assert lrc(range(10), 16, COMPLEMENT_ONES) == 65490


def testLRCCase10():
    assert lrc(range(100), 16, COMPLEMENT_ONES) == 60585


def testLRCCase11():
    assert lrc(range(10), 16, COMPLEMENT_TWOS) == 65491


def testLRCCase12():
    assert lrc(range(100), 16, COMPLEMENT_TWOS) == 60586


def testLRCCase13():
    assert lrc(range(10), 32, COMPLEMENT_NONE) == 45


def testLRCCase14():
    assert lrc(range(100), 32, COMPLEMENT_NONE) == 4950


def testLRCCase15():
    assert lrc(range(10), 32, COMPLEMENT_ONES) == 4294967250


def testLRCCase16():
    assert lrc(range(100), 32, COMPLEMENT_ONES) == 4294962345


def testLRCCase17():
    assert lrc(range(10), 32, COMPLEMENT_TWOS) == 4294967251


def testLRCCase18():
    assert lrc(range(100), 32, COMPLEMENT_TWOS) == 4294962346


def testRXORCase1():
    assert rotatedXOR(range(10), 8, ROTATE_LEFT) == 74


def testRXORCase2():
    assert rotatedXOR(range(100), 8, ROTATE_LEFT) == 66


def testRXORCase3():
    assert rotatedXOR(range(10), 8, ROTATE_RIGHT) == 186


def testRXORCase4():
    assert rotatedXOR(range(100), 8, ROTATE_RIGHT) == 3


def testRXORCase5():
    assert rotatedXOR(range(10), 16, ROTATE_LEFT) == 74


def testRXORCase6():
    assert rotatedXOR(range(100), 16, ROTATE_LEFT) == 66


def testRXORCase7():
    assert rotatedXOR(range(10), 16, ROTATE_RIGHT) == 186


def testRXORCase8():
    assert rotatedXOR(range(100), 16, ROTATE_RIGHT) == 3


def testRXORCase9():
    assert rotatedXOR(range(10), 32, ROTATE_LEFT) == 74


def testRXORCase10():
    assert rotatedXOR(range(100), 32, ROTATE_LEFT) == 66


def testRXORCase11():
    assert rotatedXOR(range(10), 32, ROTATE_RIGHT) == 186


def testRXORCase12():
    assert rotatedXOR(range(100), 32, ROTATE_RIGHT) == 3


TEST = bytes(
    (
        0x01,
        0x02,
        0x03,
        0x04,
        0x05,
        0x06,
        0x07,
        0x08,
        0x09,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x0E,
        0x0F,
        0x10,
        0xF1,
        0xF2,
        0xF3,
        0xF4,
        0xF5,
        0xF6,
        0xF7,
        0xF8,
        0xF9,
        0xFA,
        0xFB,
        0xFC,
        0xFD,
        0xFE,
        0xFF,
        0x00,
    )
)


def testAdd11():
    assert check(TEST, "CHK_ADD_11") == 0x10


def testAdd12():
    assert check(TEST, "CHK_ADD_12") == 0x0F10


def testAdd14():
    assert check(TEST, "CHK_ADD_14") == 0x00000F10


def testAdd22():
    assert check(TEST, "CHK_ADD_22") == 0x1800


def testAdd24():
    assert check(TEST, "CHK_ADD_24") == 0x00071800


def testAdd44():
    assert check(TEST, "CHK_ADD_44") == 0x140C03F8


def testCrc16():
    assert check(TEST, "CHK_CRC_16") == 0xC76A


def testCrc16Ccitt():
    assert check(TEST, "CHK_CRC_16_CCITT") == 0x9D50


@pytest.mark.parametrize(
    "x, expected",
    [
        ([0x00, 0x00, 0x00, 0x00], 0x84C0),
        ([0xF2, 0x01, 0x83], 0xD374),
        ([0x0F, 0xAA, 0x00, 0x55], 0x2023),
        ([0x00, 0xFF, 0x55, 0x11], 0xB8F9),
        ([0x33, 0x22, 0x55, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF], 0xF53F),
        ([0x92, 0x6B, 0x55], 0x0745),
        ([0xFF, 0xFF, 0xFF, 0xFF], 0x1D0F),
    ],
)
def test_crc16_ccitt_ar(x, expected):
    assert check(x, "CHK_CRC_16_CCITT") == expected


@pytest.mark.parametrize(
    "x, expected",
    [
        ((0x00, 0x00, 0x00, 0x00), 0x2144DF1C),
        ([0xF2, 0x01, 0x83], 0x24AB9D77),
        ([0x0F, 0xAA, 0x00, 0x55], 0xB6C9B287),
        ([0x00, 0xFF, 0x55, 0x11], 0x32A06212),
        ([0x33, 0x22, 0x55, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF], 0xB0AE863D),
        ([0x92, 0x6B, 0x55], 0x9CDEA29B),
        ([0xFF, 0xFF, 0xFF, 0xFF], 0xFFFFFFFF),
    ],
)
def test_crc32_ar(x, expected):
    assert check(x, "CHK_CRC_32") == expected


def testCrc32():
    assert check(TEST, "CHK_CRC_32") == 0x89CD97CE


def testUserDefined():
    with pytest.raises(NotImplementedError):
        check(TEST, "CHK_USER_DEFINED")
