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


def test_write_asam_numeric_msb_first_msw_last_uword():
    sec = Section(data=bytearray(4))
    sec.write_asam_numeric(0, 0x1234, "UWORD", byte_order="MSB_FIRST_MSW_LAST")
    assert sec.data[:2] == bytearray([0x34, 0x12])


def test_read_asam_numeric_msb_first_msw_last_uword():
    sec = Section(data=bytearray([0x34, 0x12, 0x00, 0x00]))
    assert sec.read_asam_numeric(0, "UWORD", byte_order="MSB_FIRST_MSW_LAST") == 0x1234


def test_write_asam_numeric_msb_last_msw_first_ulong():
    sec = Section(data=bytearray(8))
    sec.write_asam_numeric(0, 0x11223344, "ULONG", byte_order="MSB_LAST_MSW_FIRST")
    assert sec.data[:4] == bytearray([0x33, 0x44, 0x11, 0x22])


def test_read_asam_numeric_msb_last_msw_first_ulong():
    sec = Section(data=bytearray([0x33, 0x44, 0x11, 0x22, 0x00, 0x00, 0x00, 0x00]))
    assert sec.read_asam_numeric(0, "ULONG", byte_order="MSB_LAST_MSW_FIRST") == 0x11223344


def test_write_asam_numeric_msb_last_msw_first_a_uint64():
    sec = Section(data=bytearray(16))
    sec.write_asam_numeric(0, 0x1122334455667788, "A_UINT64", byte_order="MSB_LAST_MSW_FIRST")
    assert sec.data[:8] == bytearray([0x77, 0x88, 0x55, 0x66, 0x33, 0x44, 0x11, 0x22])


def test_read_asam_numeric_msb_last_msw_first_a_uint64():
    sec = Section(data=bytearray([0x77, 0x88, 0x55, 0x66, 0x33, 0x44, 0x11, 0x22] + [0x00] * 8))
    assert sec.read_asam_numeric(0, "A_UINT64", byte_order="MSB_LAST_MSW_FIRST") == 0x1122334455667788


def test_asam_byteorder_aliases_legacy_names():
    sec = Section(data=bytearray(4))
    sec.write_asam_numeric(0, 0x1234, "UWORD", byte_order="BIG_ENDIAN")
    assert sec.data[:2] == bytearray([0x12, 0x34])
    sec.write_asam_numeric(0, 0x1234, "UWORD", byte_order="LITTLE_ENDIAN")
    assert sec.data[:2] == bytearray([0x34, 0x12])


def test_asam_string_utf8_roundtrip():
    sec = Section(data=bytearray(64))
    sec.write_asam_string(0, "Grüße", "UTF8")
    assert sec.read_asam_string(0, "UTF8") == "Grüße"


def test_asam_float16_ieee_roundtrip():
    sec = Section(data=bytearray(8))
    sec.write_asam_numeric(0, 1.5, "FLOAT16_IEEE", byte_order="MSB_LAST")
    assert sec.read_asam_numeric(0, "FLOAT16_IEEE", byte_order="MSB_LAST") == pytest.approx(1.5, rel=1e-3)


def test_write_asam_numeric_array_msb_last_msw_first_ulong():
    sec = Section(data=bytearray(16))
    sec.write_asam_numeric_array(0, [0x11223344, 0x55667788], "ULONG", byte_order="MSB_LAST_MSW_FIRST")
    assert sec.data[:8] == bytearray([0x33, 0x44, 0x11, 0x22, 0x77, 0x88, 0x55, 0x66])


def test_read_asam_numeric_array_msb_last_msw_first_ulong():
    sec = Section(data=bytearray([0x33, 0x44, 0x11, 0x22, 0x77, 0x88, 0x55, 0x66] + [0x00] * 8))
    assert sec.read_asam_numeric_array(0, 2, "ULONG", byte_order="MSB_LAST_MSW_FIRST") == (0x11223344, 0x55667788)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_write_asam_ndarray_msb_last_msw_first_ulong():
    sec = Section(start_address=0x1000, data=bytearray(32))
    arr = np.array([0x11223344, 0x55667788], dtype=np.uint32)
    sec.write_asam_ndarray(0x1000, arr, "ULONG", byte_order="MSB_LAST_MSW_FIRST")
    assert sec.read(0x1000, 8) == bytearray([0x33, 0x44, 0x11, 0x22, 0x77, 0x88, 0x55, 0x66])


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_read_asam_ndarray_msb_last_msw_first_ulong():
    sec = Section(start_address=0x1000, data=bytearray([0x33, 0x44, 0x11, 0x22, 0x77, 0x88, 0x55, 0x66] + [0x00] * 24))
    result = sec.read_asam_ndarray(0x1000, 2, "ULONG", shape=(2,), byte_order="MSB_LAST_MSW_FIRST")
    assert np.array_equal(result, np.array([0x11223344, 0x55667788], dtype=np.uint32))


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_column_dir_roundtrip():
    """Replaces the old test_asam_ndarray_fortran_roundtrip."""
    sec = Section(start_address=0x1000, data=bytearray(32))
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
    sec.write_asam_ndarray(0x1000, arr, "UWORD", byte_order="MSB_FIRST_MSW_LAST", index_mode="COLUMN_DIR")
    assert sec.read(0x1000, 12) == bytearray(b"\x01\x00\x04\x00\x02\x00\x05\x00\x03\x00\x06\x00")
    result = sec.read_asam_ndarray(0x1000, 6, "UWORD", shape=(3, 2), index_mode="COLUMN_DIR", byte_order="MSB_FIRST_MSW_LAST")
    assert np.array_equal(result, arr)


# ---------------------------------------------------------------------------
# ASAM ndarray: ROW_DIR / COLUMN_DIR / shape reversal / element count
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_row_dir_2d_val_blk():
    """ASAM VAL_BLK: MATRIX_DIM 5 4, ROW_DIR."""
    row_dir_flat = [
        11,
        21,
        31,
        41,
        51,
        12,
        22,
        32,
        42,
        52,
        13,
        23,
        33,
        43,
        53,
        14,
        24,
        34,
        44,
        54,
    ]
    sec = Section(start_address=0x1000, data=bytearray(64))
    arr = np.array(row_dir_flat, dtype=np.uint8).reshape(4, 5)
    sec.write_asam_ndarray(0x1000, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ROW_DIR")
    assert list(sec.read(0x1000, 20)) == row_dir_flat
    result = sec.read_asam_ndarray(0x1000, 20, "UBYTE", shape=(5, 4), byte_order="MSB_LAST", index_mode="ROW_DIR")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_column_dir_2d_val_blk():
    """ASAM VAL_BLK: MATRIX_DIM 5 4, COLUMN_DIR."""
    col_dir_flat = [
        11,
        12,
        13,
        14,
        21,
        22,
        23,
        24,
        31,
        32,
        33,
        34,
        41,
        42,
        43,
        44,
        51,
        52,
        53,
        54,
    ]
    expected_numpy = np.array(
        [
            [11, 21, 31, 41, 51],
            [12, 22, 32, 42, 52],
            [13, 23, 33, 43, 53],
            [14, 24, 34, 44, 54],
        ],
        dtype=np.uint8,
    )
    sec = Section(start_address=0x1000, data=bytearray(col_dir_flat + [0] * 44))
    result = sec.read_asam_ndarray(0x1000, 20, "UBYTE", shape=(5, 4), byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    assert result.shape == (4, 5)
    assert np.array_equal(result, expected_numpy)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_column_dir_2d_write_roundtrip():
    """Write COLUMN_DIR, verify raw memory, read back."""
    arr = np.array(
        [
            [11, 21, 31, 41, 51],
            [12, 22, 32, 42, 52],
            [13, 23, 33, 43, 53],
            [14, 24, 34, 44, 54],
        ],
        dtype=np.uint8,
    )
    sec = Section(start_address=0x1000, data=bytearray(64))
    sec.write_asam_ndarray(0x1000, arr, "UBYTE", byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    expected_memory = [11, 12, 13, 14, 21, 22, 23, 24, 31, 32, 33, 34, 41, 42, 43, 44, 51, 52, 53, 54]
    assert list(sec.read(0x1000, 20)) == expected_memory
    result = sec.read_asam_ndarray(0x1000, 20, "UBYTE", shape=(5, 4), byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_shape_reversal_1d():
    """1-D shape (N,) survives reversal unchanged."""
    sec = Section(start_address=0, data=bytearray(16))
    arr = np.array([10, 20, 30, 40], dtype=np.uint16)
    sec.write_asam_ndarray(0, arr, "UWORD", byte_order="MSB_LAST")
    result = sec.read_asam_ndarray(0, 4, "UWORD", shape=(4,), byte_order="MSB_LAST")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_row_dir_uword_le():
    """ROW_DIR with UWORD little-endian, element-count semantics."""
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
    sec = Section(start_address=0x2000, data=bytearray(32))
    sec.write_asam_ndarray(0x2000, arr, "UWORD", byte_order="MSB_LAST", index_mode="ROW_DIR")
    assert sec.read(0x2000, 12) == b"\x01\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00"
    result = sec.read_asam_ndarray(0x2000, 6, "UWORD", shape=(3, 2), byte_order="MSB_LAST", index_mode="ROW_DIR")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_column_dir_3d():
    """3-D COLUMN_DIR: only X and Y swapped, Z stays C-order."""
    arr = np.arange(1, 13, dtype=np.uint8).reshape(2, 2, 3)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    expected_flat = [1, 4, 2, 5, 3, 6, 7, 10, 8, 11, 9, 12]
    assert list(sec.read(0, 12)) == expected_flat
    result = sec.read_asam_ndarray(0, 12, "UBYTE", shape=(3, 2, 2), byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    assert result.shape == (2, 2, 3)
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_invalid_index_mode():
    """Unsupported index_mode must raise ValueError."""
    sec = Section(start_address=0, data=bytearray(16))
    arr = np.array([1, 2, 3], dtype=np.uint8)
    with pytest.raises(ValueError):
        sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="INVALID")
    with pytest.raises(ValueError):
        sec.read_asam_ndarray(0, 3, "UBYTE", shape=(3,), byte_order="MSB_LAST", index_mode="INVALID")


# ---------------------------------------------------------------------------
# ASAM numeric_array ↔ ndarray cross-function roundtrip tests
# ---------------------------------------------------------------------------


def test_asam_numeric_array_sword_roundtrip():
    """write_asam_numeric_array → read_asam_numeric_array: SWORD, MSB_LAST."""
    values = (1, -2, 3, -4, 5, -6, 7, -8, 9, -10, 11, -12)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_numeric_array(0, values, "SWORD", byte_order="MSB_LAST")
    result = sec.read_asam_numeric_array(0, 12, "SWORD", byte_order="MSB_LAST")
    assert result == values


def test_asam_numeric_array_ulong_roundtrip():
    """write_asam_numeric_array → read_asam_numeric_array: ULONG, MSB_LAST."""
    values = (0xDEADBEEF, 0xCAFEBABE, 0x12345678)
    sec = Section(start_address=0, data=bytearray(16))
    sec.write_asam_numeric_array(0, values, "ULONG", byte_order="MSB_LAST")
    result = sec.read_asam_numeric_array(0, 3, "ULONG", byte_order="MSB_LAST")
    assert result == values


def test_asam_numeric_array_ulong_msb_first_roundtrip():
    """write_asam_numeric_array → read_asam_numeric_array: ULONG, MSB_FIRST."""
    values = (0x11223344, 0x55667788, 0xAABBCCDD)
    sec = Section(start_address=0, data=bytearray(16))
    sec.write_asam_numeric_array(0, values, "ULONG", byte_order="MSB_FIRST")
    result = sec.read_asam_numeric_array(0, 3, "ULONG", byte_order="MSB_FIRST")
    assert result == values


def test_asam_numeric_array_msb_last_msw_first_roundtrip():
    """write_asam_numeric_array → read_asam_numeric_array: word-swap variant."""
    values = (0x11223344, 0x55667788)
    sec = Section(start_address=0, data=bytearray(16))
    sec.write_asam_numeric_array(0, values, "ULONG", byte_order="MSB_LAST_MSW_FIRST")
    result = sec.read_asam_numeric_array(0, 2, "ULONG", byte_order="MSB_LAST_MSW_FIRST")
    assert result == values


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_numeric_array_float32_roundtrip():
    """write_asam_numeric_array → read_asam_numeric_array: FLOAT32_IEEE."""
    values = (1.5, -2.25, 3.0, 0.0)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_numeric_array(0, values, "FLOAT32_IEEE", byte_order="MSB_LAST")
    result = sec.read_asam_numeric_array(0, 4, "FLOAT32_IEEE", byte_order="MSB_LAST")
    for got, expected in zip(result, values):
        assert got == pytest.approx(expected, abs=1e-6)


# ---------------------------------------------------------------------------
# Cross-function: write_asam_numeric_array → read_asam_ndarray
# (flat write, shaped read — verifies memory layout consistency)
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_cross_numeric_array_to_ndarray_row_dir_sword():
    """write_asam_numeric_array (flat, C-order) → read_asam_ndarray ROW_DIR.

    ASAM shape (3, 4) → numpy shape (4, 3).
    C-order memory: row-by-row → 1 2 3 | 4 5 6 | 7 8 9 | 10 11 12.
    """
    flat_c = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    expected = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=np.int16)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_numeric_array(0, flat_c, "SWORD", byte_order="MSB_LAST")
    result = sec.read_asam_ndarray(0, 12, "SWORD", shape=(3, 4), index_mode="ROW_DIR", byte_order="MSB_LAST")
    assert result.shape == (4, 3)
    assert np.array_equal(result, expected)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_cross_numeric_array_to_ndarray_column_dir_sword():
    """write_asam_numeric_array (flat, column-order) → read_asam_ndarray COLUMN_DIR.

    ASAM shape (3, 4) → numpy shape (4, 3).
    COLUMN_DIR memory: column-by-column → 1 4 7 10 | 2 5 8 11 | 3 6 9 12.
    Both must yield the same logical array [[1,2,3],[4,5,6],[7,8,9],[10,11,12]].
    """
    flat_f = [1, 4, 7, 10, 2, 5, 8, 11, 3, 6, 9, 12]
    expected = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=np.int16)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_numeric_array(0, flat_f, "SWORD", byte_order="MSB_LAST")
    result = sec.read_asam_ndarray(0, 12, "SWORD", shape=(3, 4), index_mode="COLUMN_DIR", byte_order="MSB_LAST")
    assert result.shape == (4, 3)
    assert np.array_equal(result, expected)


# ---------------------------------------------------------------------------
# Cross-function: write_asam_ndarray → read_asam_numeric_array
# (shaped write, flat read — verifies memory layout consistency)
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_cross_ndarray_to_numeric_array_row_dir_sword():
    """write_asam_ndarray ROW_DIR → read_asam_numeric_array (flat).

    Expected flat tuple: C-order row-by-row.
    """
    arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=np.int16)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_ndarray(0, arr, "SWORD", byte_order="MSB_LAST", index_mode="ROW_DIR")
    result = sec.read_asam_numeric_array(0, 12, "SWORD", byte_order="MSB_LAST")
    assert result == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_cross_ndarray_to_numeric_array_column_dir_sword():
    """write_asam_ndarray COLUMN_DIR → read_asam_numeric_array (flat).

    Expected flat tuple: column-by-column (Y increments fastest).
    """
    arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=np.int16)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_ndarray(0, arr, "SWORD", byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    result = sec.read_asam_numeric_array(0, 12, "SWORD", byte_order="MSB_LAST")
    assert result == (1, 4, 7, 10, 2, 5, 8, 11, 3, 6, 9, 12)


# ---------------------------------------------------------------------------
# Full roundtrip: write_asam_ndarray → read_asam_ndarray (various configs)
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_full_roundtrip_row_dir_sword():
    """write ROW_DIR → read ROW_DIR: SWORD, shape (3, 4)."""
    arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=np.int16)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_ndarray(0, arr, "SWORD", byte_order="MSB_LAST", index_mode="ROW_DIR")
    result = sec.read_asam_ndarray(0, 12, "SWORD", shape=(3, 4), index_mode="ROW_DIR", byte_order="MSB_LAST")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_full_roundtrip_column_dir_sword():
    """write COLUMN_DIR → read COLUMN_DIR: SWORD, shape (3, 4)."""
    arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=np.int16)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_ndarray(0, arr, "SWORD", byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    result = sec.read_asam_ndarray(0, 12, "SWORD", shape=(3, 4), index_mode="COLUMN_DIR", byte_order="MSB_LAST")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_full_roundtrip_column_dir_ulong_msb_first():
    """write COLUMN_DIR → read COLUMN_DIR: ULONG, MSB_FIRST, shape (2, 3)."""
    arr = np.array([[100, 200], [300, 400], [500, 600]], dtype=np.uint32)
    sec = Section(start_address=0x4000, data=bytearray(64))
    sec.write_asam_ndarray(0x4000, arr, "ULONG", byte_order="MSB_FIRST", index_mode="COLUMN_DIR")
    result = sec.read_asam_ndarray(0x4000, 6, "ULONG", shape=(2, 3), index_mode="COLUMN_DIR", byte_order="MSB_FIRST")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_full_roundtrip_row_dir_ulong_word_swap():
    """write ROW_DIR → read ROW_DIR: ULONG, MSB_LAST_MSW_FIRST (word-swap), shape (2, 2)."""
    arr = np.array([[0x11223344, 0x55667788], [0xAABBCCDD, 0xEEFF0011]], dtype=np.uint32)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_ndarray(0, arr, "ULONG", byte_order="MSB_LAST_MSW_FIRST", index_mode="ROW_DIR")
    result = sec.read_asam_ndarray(0, 4, "ULONG", shape=(2, 2), index_mode="ROW_DIR", byte_order="MSB_LAST_MSW_FIRST")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_full_roundtrip_column_dir_uword_3x5():
    """write COLUMN_DIR → read COLUMN_DIR: UWORD, shape (3, 5) — wider matrix."""
    arr = np.arange(1, 16, dtype=np.uint16).reshape(5, 3)
    sec = Section(start_address=0x1000, data=bytearray(64))
    sec.write_asam_ndarray(0x1000, arr, "UWORD", byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    result = sec.read_asam_ndarray(0x1000, 15, "UWORD", shape=(3, 5), index_mode="COLUMN_DIR", byte_order="MSB_LAST")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_asam_ndarray_full_roundtrip_row_dir_ubyte_1d():
    """1-D roundtrip: index_mode irrelevant for 1-D, but must still work."""
    arr = np.array([10, 20, 30, 40, 50], dtype=np.uint8)
    sec = Section(start_address=0, data=bytearray(16))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ROW_DIR")
    result = sec.read_asam_ndarray(0, 5, "UBYTE", shape=(5,), index_mode="ROW_DIR", byte_order="MSB_LAST")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_cross_ndarray_to_numeric_array_column_dir_3d():
    """write_asam_ndarray COLUMN_DIR 3D → read_asam_numeric_array (flat).

    For 3D, only the last two dims are column-ordered per slice.
    arr shape (2, 2, 3) → ASAM shape (3, 2, 2).
    """
    arr = np.arange(1, 13, dtype=np.uint8).reshape(2, 2, 3)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    flat = sec.read_asam_numeric_array(0, 12, "UBYTE", byte_order="MSB_LAST")
    assert flat == (1, 4, 2, 5, 3, 6, 7, 10, 8, 11, 9, 12)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_cross_numeric_array_to_ndarray_column_dir_3d():
    """write_asam_numeric_array (flat 3D COLUMN_DIR) → read_asam_ndarray COLUMN_DIR.

    Verifies the inverse of the previous test.
    """
    flat_col = [1, 4, 2, 5, 3, 6, 7, 10, 8, 11, 9, 12]
    expected = np.arange(1, 13, dtype=np.uint8).reshape(2, 2, 3)
    sec = Section(start_address=0, data=bytearray(32))
    sec.write_asam_numeric_array(0, flat_col, "UBYTE", byte_order="MSB_LAST")
    result = sec.read_asam_ndarray(0, 12, "UBYTE", shape=(3, 2, 2), index_mode="COLUMN_DIR", byte_order="MSB_LAST")
    assert result.shape == (2, 2, 3)
    assert np.array_equal(result, expected)
