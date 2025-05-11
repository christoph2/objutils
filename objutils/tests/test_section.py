import array
import math
import struct

import pytest

from objutils.exceptions import InvalidAddressError
from objutils.section import (
    INT8_RANGE,
    INT16_RANGE,
    INT32_RANGE,
    INT64_RANGE,
    UINT8_RANGE,
    UINT16_RANGE,
    UINT32_RANGE,
    UINT64_RANGE,
    Section,
    filler,
)


try:
    import numpy as np
except ImportError:
    NUMPY_SUPPORT = False
else:
    NUMPY_SUPPORT = True


def test_default_section():
    section = Section()
    # section = Section2(data=[10, 20, 30, 40])
    assert section.start_address == 0
    assert section.length == 0
    assert section.data == b""


def test_default_startAddress():
    section = Section(start_address=0x10000)
    assert section.start_address == 0x10000
    assert section.length == 0
    assert section.data == b""


def test_initialize_from_list():
    section = Section(data=[10, 20, 30, 40])
    assert section.start_address == 0
    assert section.length == 4
    assert section.data == b"\n\x14\x1e("


def test_initialize_from_array1():
    section = Section(data=array.array("B", [10, 20, 30, 40]))
    assert section.start_address == 0
    assert section.length == 4
    assert section.data == b"\n\x14\x1e("


def test_initialize_from_array2():
    section = Section(data=array.array("H", [0x1010, 0x2020, 0x3030, 0x4040]))
    assert section.start_address == 0
    assert section.length == 8
    assert section.data == b"\x10\x10  00@@"


def test_initialize_from_range():
    section = Section(data=range(16))
    assert section.start_address == 0
    assert section.length == 16
    assert section.data == b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f"


def test_initialize_from_string():
    section = Section(data="abcd")
    assert section.start_address == 0
    assert section.length == 4
    assert section.data == b"abcd"


def test_adress_in_range1():
    s0 = Section(start_address=0x10, data="hello")
    assert 0x10 in s0


def test_adress_in_range2():
    s0 = Section(start_address=0x10, data="hello")
    assert 0x14 in s0


def test_adress_out_of_range1():
    s0 = Section(start_address=0x10, data="hello")
    assert 0x09 not in s0


def test_adress_out_of_range2():
    s0 = Section(start_address=0x10, data="hello")
    assert 0x15 not in s0


def test_copy_data_from_other_section():
    data = Section(data="abcd", start_address=0x8000)
    section = Section(data=data)
    assert section.start_address == 0
    assert section.length == 4
    assert section.data == b"abcd"


def test_copy_really_works():
    section1 = Section(data=range(16), start_address=0x8000)
    section2 = Section(data=section1)
    assert section2.start_address == 0
    assert section2.length == 16
    assert section2.data == b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f"
    assert section2.data == section1.data
    section2.write_numeric(0, 0xFF, "uint8_le")
    assert section2.data == b"\xff\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f"
    assert section1.data != section2.data


def test_single_int_not_permitted():
    with pytest.raises(ValueError):
        Section(data=42)


def test_filler1():
    assert filler(0x00, 16) == b"\x00" * 16


def test_filler2():
    assert filler(0xFF, 16) == b"\xff" * 16


def test_filler_fails1():
    with pytest.raises(ValueError):
        filler(0xFF, 0)


def test_filler_fails2():
    with pytest.raises(ValueError):
        filler(1000, 10)


def test_filler_fails3():
    with pytest.raises(TypeError):
        filler("hello", 10)


def test_filler_fails4():
    with pytest.raises(TypeError):
        filler(0x00, "hello")


def test_int8_range():
    assert INT8_RANGE == (-128, 127)


def test_uint8_range():
    assert UINT8_RANGE == (0, 255)


def test_uint16_range():
    assert UINT16_RANGE == (0, 65535)


def test_int16_range():
    assert INT16_RANGE == (-32768, 32767)


def test_int32_range():
    assert INT32_RANGE == (-2147483648, 2147483647)


def test_uint32_range():
    assert UINT32_RANGE == (0, 4294967295)


def test_int64_range():
    assert INT64_RANGE == (-9223372036854775808, 9223372036854775808)


def test_uint64_range():
    assert UINT64_RANGE == (0, 18446744073709551615)


@pytest.fixture
def filler_0_16():
    return Section(data=filler(0x00, 16))


def test_write_uint8_le1(filler_0_16):
    filler_0_16.write_numeric(0, 0xFF, "uint8_le")
    assert filler_0_16.data == bytearray([0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_uint8_le2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.lower - 1, "uint8_le")


def test_write_uint8_le3(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.upper + 1, "uint8_le")


def test_write_uint8_be1(filler_0_16):
    filler_0_16.write_numeric(0, 0xFF, "uint8_be")
    assert filler_0_16.data == bytearray([0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_uint8_be2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.lower - 1, "uint8_be")


def test_write_uint8_be3(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.upper + 1, "uint8_be")


def test_write_int8_le1(filler_0_16):
    filler_0_16.write_numeric(0, -100, "int8_le")
    assert filler_0_16.data == bytearray([0x9C, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_int8_le2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.lower - 1, "int8_le")


def test_write_int8_le3(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.upper + 1, "int8_le")


def test_write_int8_be1(filler_0_16):
    filler_0_16.write_numeric(0, -100, "int8_be")
    assert filler_0_16.data == bytearray([0x9C, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_int8_be2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.lower - 1, "int8_be")


def test_write_int8_be3(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.upper + 1, "int8_be")


##
##
def test_write_byte0(filler_0_16):
    filler_0_16.write_numeric(0, 0xFF, "byte")
    assert filler_0_16.data == bytearray([0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_byte1(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.lower - 1, "byte")


def test_write_byte2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.upper + 1, "byte")


def test_write_byte3(filler_0_16):
    filler_0_16.write_numeric(0, 0xFF, "byte")
    assert filler_0_16.data == bytearray([0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_byte4(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.lower - 1, "byte")


def test_write_byte5(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.upper + 1, "byte")


def test_write_byte6(filler_0_16):
    with pytest.raises(struct.error):  # noqa: B908
        filler_0_16.write_numeric(0, -100, "byte")  # Negative numbers are not permitted.
        assert filler_0_16.data == bytearray([0x9C, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_byte7(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.lower - 1, "byte")


@pytest.mark.skip
def test_write_byte8(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.upper + 1, "byte")


@pytest.mark.skip
def test_write_byte9(filler_0_16):
    filler_0_16.write_numeric(0, -100, "byte")
    assert filler_0_16.data == bytearray([0x9C, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_byte10(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.lower - 1, "byte")


@pytest.mark.skip
def test_write_byte11(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.upper + 1, "byte")


##
##


def test_write_uint16_le1(filler_0_16):
    filler_0_16.write_numeric(0, 0x1122, "uint16_le")
    assert filler_0_16.data == bytearray([0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_uint16_be1(filler_0_16):
    filler_0_16.write_numeric(0, 0x1122, "uint16_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_int16_le1(filler_0_16):
    filler_0_16.write_numeric(0, -20000, "int16_le")
    assert filler_0_16.data == bytearray([0xE0, 0xB1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_int16_be1(filler_0_16):
    filler_0_16.write_numeric(0, -20000, "int16_be")
    assert filler_0_16.data == bytearray([0xB1, 0xE0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_uint32_le1(filler_0_16):
    filler_0_16.write_numeric(0, 0x11223344, "uint32_le")
    assert filler_0_16.data == bytearray([0x44, 0x33, 0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_uint32_be1(filler_0_16):
    filler_0_16.write_numeric(0, 0x11223344, "uint32_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0x33, 0x44, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_int32_le1(filler_0_16):
    filler_0_16.write_numeric(0, -3000000, "int32_le")
    assert filler_0_16.data == bytearray([0x40, 0x39, 0xD2, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_int32_be1(filler_0_16):
    filler_0_16.write_numeric(0, -3000000, "int32_be")
    assert filler_0_16.data == bytearray([0xFF, 0xD2, 0x39, 0x40, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_uint64_le1(filler_0_16):
    filler_0_16.write_numeric(0, 0x1122334455667788, "uint64_le")
    assert filler_0_16.data == bytearray([0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_uint64_be1(filler_0_16):
    filler_0_16.write_numeric(0, 0x1122334455667788, "uint64_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_int64_le1(filler_0_16):
    filler_0_16.write_numeric(0, -400000000, "int64_le")
    assert filler_0_16.data == bytearray([0x0, 0x7C, 0x28, 0xE8, 0xFF, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_int64_be1(filler_0_16):
    filler_0_16.write_numeric(0, -400000000, "int64_be")
    assert filler_0_16.data == bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xE8, 0x28, 0x7C, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_float32_le1(filler_0_16):
    filler_0_16.write_numeric(0, math.pi, "float32_le")
    assert filler_0_16.data == bytearray([0xDB, 0x0F, 0x49, 0x40, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_float32_be1(filler_0_16):
    filler_0_16.write_numeric(0, math.pi, "float32_be")
    assert filler_0_16.data == bytearray([0x40, 0x49, 0x0F, 0xDB, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_float64_le1(filler_0_16):
    filler_0_16.write_numeric(0, math.pi, "float64_le")
    assert filler_0_16.data == bytearray([0x18, 0x2D, 0x44, 0x54, 0xFB, 0x21, 0x09, 0x40, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_float64_be1(filler_0_16):
    filler_0_16.write_numeric(0, math.pi, "float64_be")
    assert filler_0_16.data == bytearray([0x40, 0x09, 0x21, 0xFB, 0x54, 0x44, 0x2D, 0x18, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write_uint8_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 0xFF, "uint8_le")


def test_write_uint16_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 0xFF, "uint16_le")


def test_write_uint32_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 0xFF, "uint32_le")


def test_write_uint64_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 0xFF, "uint64_le")


def test_write_int8_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 0xFF, "int8_le")


def test_write_int16_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 0xFF, "int16_le")


def test_write_int32_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 0xFF, "int32_le")


def test_write_int64_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 0xFF, "int64_le")


def test_write_float32_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 3.14159, "float32_le")


def test_write_float64_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric(-1, 3.14159, "float64_le")


def test_read_uint8_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "uint8_le")


def test_read_uint16_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "uint16_le")


def test_read_uint32_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "uint32_le")


def test_read_uint64_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "uint64_le")


def test_read_int8_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "int8_le")


def test_read_int16_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "int16_le")


def test_read_int32_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "int32_le")


def test_read_int64_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "int64_le")


def test_read_float32_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "float32_le")


def test_read_float64_negative_offset(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read_numeric(-1, "float64_le")


def test_write_boundary_case1(filler_0_16):
    filler_0_16.write(0x0, b"hello")


def test_write_boundary_case2(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write(0x10, b"hello")


def test_write_boundary_case3(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write(-1, b"hello")


def test_read_boundary_case1(filler_0_16):
    assert filler_0_16.read(0x0, 5) == b"\x00\x00\x00\x00\x00"


def test_read_boundary_case2(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read(0x10, 5)


def test_read_boundary_case3(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.read(-1, 5)


def test_read_uint8_array_boundary_case1(filler_0_16):
    assert filler_0_16.read_numeric_array(0, 10, "uint8_be") == (
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )


def test_read_uint8_array_boundary_case2(filler_0_16):
    with pytest.raises(InvalidAddressError):
        assert filler_0_16.read_numeric_array(0x10, 10, "uint8_be") == (
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        )


def test_read_uint8_array_boundary_case3(filler_0_16):
    with pytest.raises(InvalidAddressError):
        assert filler_0_16.read_numeric_array(-1, 10, "uint8_be") == (
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        )


def test_write_uint8_array_boundary_case1(filler_0_16):
    filler_0_16.write_numeric_array(0, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")


def test_write_uint8_array_boundary_case2(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric_array(0x10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")


def test_write_uint8_array_boundary_case3(filler_0_16):
    with pytest.raises(InvalidAddressError):
        filler_0_16.write_numeric_array(-1, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_write_ndarray1():
    sec = Section(start_address=0x1000, data=bytearray(32))
    arr = np.array([[11, 22, 33], [44, 55, 66]], dtype="int32")
    sec.write_ndarray(0x1000, arr)
    assert (
        sec.data
        == b"\x0b\x00\x00\x00\x16\x00\x00\x00!\x00\x00\x00,\x00\x00\x007\x00\x00\x00B\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_write_ndarray_out_of_bounds1():
    sec = Section(start_address=0x1000, data=bytearray(32))
    arr = np.array([[11, 22, 33], [44, 55, 66]], dtype="int64")
    with pytest.raises(InvalidAddressError):
        sec.write_ndarray(0x1000, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_write_ndarray_out_of_bounds2():
    sec = Section(start_address=0x1000, data=bytearray(32))
    arr = np.array([[11, 22, 33], [44, 55, 66]], dtype="int64")
    with pytest.raises(InvalidAddressError):
        sec.write_ndarray(0x9FF, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_read_ndarray_reshaped():
    sec = Section(start_address=0x1000, data=bytearray(32))
    arr = np.array([[11, 22, 33], [44, 55, 66]], dtype="int32")
    sec.write_ndarray(0x1000, arr)

    result = sec.read_ndarray(0x1000, 24, "int32_le", shape=(2, 3))
    assert np.array_equal(result, np.array([[11, 22, 33], [44, 55, 66]]))


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_read_ndarray_flat():
    sec = Section(start_address=0x1000, data=bytearray(32))
    arr = np.array([[11, 22, 33], [44, 55, 66]], dtype="int32")
    sec.write_ndarray(0x1000, arr)

    result = sec.read_ndarray(0x1000, 24, "int32_le")
    assert np.array_equal(result, np.array([11, 22, 33, 44, 55, 66]))


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_read_ndarray_fortan_01():
    sec = Section(
        start_address=0x1000,
        data=bytearray(b"\x01\x00\x04\x00\x07\x00\n\x00\x02\x00\x05\x00\x08\x00\x0b\x00\x03\x00\x06\x00\t\x00\x0c\x00"),
    )

    result = sec.read_ndarray(0x1000, 24, shape=(3, 4), order="F", dtype="int16_le")
    assert np.array_equal(
        result,
        np.array(
            [
                [1, 2, 3],
                [
                    4,
                    5,
                    6,
                ],
                [7, 8, 9],
                [10, 11, 12],
            ],
            dtype=np.int16,
        ),
    )


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_read_ndarray_fortan_02():
    sec = Section(
        start_address=0x1000,
        data=[
            1,
            3,
            5,
            2,
            4,
            6,
            7,
            9,
            11,
            8,
            10,
            12,
            13,
            15,
            17,
            14,
            16,
            18,
            19,
            21,
            23,
            20,
            22,
            24,
            25,
            27,
            29,
            26,
            28,
            30,
            31,
            33,
            35,
            32,
            34,
            36,
            37,
            39,
            41,
            38,
            40,
            42,
            43,
            45,
            47,
            44,
            46,
            48,
        ],
    )

    result = sec.read_ndarray(0x1000, 48, shape=(2, 4, 3, 2), order="F", dtype="int8_le")
    assert np.array_equal(
        result,
        np.array(
            [
                [
                    [[1, 2], [3, 4], [5, 6]],
                    [[7, 8], [9, 10], [11, 12]],
                    [[13, 14], [15, 16], [17, 18]],
                    [[19, 20], [21, 22], [23, 24]],
                ],
                [
                    [[25, 26], [27, 28], [29, 30]],
                    [[31, 32], [33, 34], [35, 36]],
                    [[37, 38], [39, 40], [41, 42]],
                    [[43, 44], [45, 46], [47, 48]],
                ],
            ],
            dtype=np.int8,
        ),
    )


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_write_ndarray_fortan_01():
    sec = Section(start_address=0x1000, data=bytearray(128))
    arr = np.array(
        [
            [[[1, 2], [3, 4], [5, 6]], [[7, 8], [9, 10], [11, 12]], [[13, 14], [15, 16], [17, 18]], [[19, 20], [21, 22], [23, 24]]],
            [
                [[25, 26], [27, 28], [29, 30]],
                [[31, 32], [33, 34], [35, 36]],
                [[37, 38], [39, 40], [41, 42]],
                [[43, 44], [45, 46], [47, 48]],
            ],
        ],
        dtype=np.int8,
    )
    sec.write_ndarray(0x1000, arr, order="F")
    assert sec.read(0x1000, 48) == bytearray(
        b"\x01\x03\x05\x02\x04\x06\x07\t\x0b\x08\n\x0c\r\x0f\x11\x0e\x10\x12\x13\x15\x17\x14\x16\x18\x19\x1b\x1d\x1a\x1c\x1e\x1f!# \"$%')&(*+-/,.0"
    )


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_write_ndarray_fortan_02():
    sec = Section(start_address=0x1000, data=bytearray(128))
    arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=np.int16)
    sec.write_ndarray(0x1000, arr, order="F")
    assert sec.read(0x1000, 24) == bytearray(
        b"\x01\x00\x04\x00\x07\x00\n\x00\x02\x00\x05\x00\x08\x00\x0b\x00\x03\x00\x06\x00\t\x00\x0c\x00"
    )
