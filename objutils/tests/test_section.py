
import array
import math
import struct

import pytest


from objutils.section import (Section, filler, INT8_RANGE, INT16_RANGE,
        INT32_RANGE, INT64_RANGE, UINT8_RANGE, UINT16_RANGE, UINT32_RANGE,
        UINT64_RANGE)


def test_default_section():
    section = Section()
    #section = Section2(data=[10, 20, 30, 40])
    assert section.start_address == 0
    assert section.length == 0
    assert section.data == b''

def test_default_startAddress():
    section = Section(start_address = 0x10000)
    assert section.start_address == 0x10000
    assert section.length == 0
    assert section.data == b''

def test_initialize_from_list():
    section = Section(data = [10, 20, 30, 40])
    assert section.start_address == 0
    assert section.length == 4
    assert section.data == b'\n\x14\x1e('

def test_initialize_from_array1():
    section = Section(data = array.array('B', [10, 20, 30, 40]))
    assert section.start_address == 0
    assert section.length == 4
    assert section.data == b'\n\x14\x1e('

def test_initialize_from_array2():
    section = Section(data = array.array('H', [0x1010, 0x2020, 0x3030, 0x4040]))
    assert section.start_address == 0
    assert section.length == 8
    assert section.data == b'\x10\x10  00@@'

def test_initialize_from_range():
    section = Section(data = range(16))
    assert section.start_address == 0
    assert section.length == 16
    assert section.data == b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'

def test_initialize_from_string():
    section = Section(data = "abcd")
    assert section.start_address == 0
    assert section.length == 4
    assert section.data == b'abcd'

def test_copy_data_from_other_section():
    data = Section(data = "abcd", start_address = 0x8000)
    section = Section(data = data)
    assert section.start_address == 0
    assert section.length == 4
    assert section.data == b'abcd'

def test_copy_really_works():
    section1 = Section(data = range(16), start_address = 0x8000)
    section2 = Section(data = section1)
    assert section2.start_address == 0
    assert section2.length == 16
    assert section2.data == b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'
    assert section2.data == section1.data
    section2.write_numeric(0, 0xff, "uint8_le")
    assert section2.data == b'\xff\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'
    assert section1.data != section2.data

def test_single_int_not_permitted():
    with pytest.raises(ValueError):
        Section(data = 42)

def test_filler1():
    assert filler(0x00, 16) == b'\x00' * 16

def test_filler2():
    assert filler(0xff, 16) == b'\xff' * 16

def test_filler_fails1():
    with pytest.raises(ValueError):
        filler(0xff, 0)

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
    return Section(data = filler(0x00, 16))

def test_write_uint8_le1(filler_0_16):
    filler_0_16.write_numeric(0, 0xff, "uint8_le")
    assert filler_0_16.data == bytearray([0xff, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint8_le2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.lower - 1, "uint8_le")

def test_write_uint8_le3(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.upper + 1, "uint8_le")

def test_write_uint8_be1(filler_0_16):
    filler_0_16.write_numeric(0, 0xff, "uint8_be")
    assert filler_0_16.data == bytearray([0xff, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint8_be2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.lower - 1, "uint8_be")

def test_write_uint8_be3(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, UINT8_RANGE.upper + 1, "uint8_be")

def test_write_int8_le1(filler_0_16):
    filler_0_16.write_numeric(0, -100, "int8_le")
    assert filler_0_16.data == bytearray([0x9c, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_int8_le2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.lower - 1, "int8_le")

def test_write_int8_le3(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.upper + 1, "int8_le")

def test_write_int8_be1(filler_0_16):
    filler_0_16.write_numeric(0, -100, "int8_be")
    assert filler_0_16.data == bytearray([0x9c, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_int8_be2(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.lower - 1, "int8_be")

def test_write_int8_be3(filler_0_16):
    with pytest.raises(struct.error):
        filler_0_16.write_numeric(0, INT8_RANGE.upper + 1, "int8_be")

def test_write_uint16_le1(filler_0_16):
    filler_0_16.write_numeric(0, 0x1122, "uint16_le")
    assert filler_0_16.data == bytearray([0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint16_be1(filler_0_16):
    filler_0_16.write_numeric(0, 0x1122, "uint16_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_int16_le1(filler_0_16):
    filler_0_16.write_numeric(0, -20000, "int16_le")
    assert filler_0_16.data == bytearray([0xe0, 0xb1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_int16_be1(filler_0_16):
    filler_0_16.write_numeric(0, -20000, "int16_be")
    assert filler_0_16.data == bytearray([0xb1, 0xe0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint32_le1(filler_0_16):
    filler_0_16.write_numeric(0, 0x11223344, "uint32_le")
    assert filler_0_16.data == bytearray([0x44, 0x33, 0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint32_be1(filler_0_16):
    filler_0_16.write_numeric(0, 0x11223344, "uint32_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0x33, 0x44, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_int32_le1(filler_0_16):
    filler_0_16.write_numeric(0, -3000000, "int32_le")
    assert filler_0_16.data == bytearray([0x40, 0x39, 0xd2, 0xff, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_int32_be1(filler_0_16):
    filler_0_16.write_numeric(0, -3000000, "int32_be")
    assert filler_0_16.data == bytearray([0xff, 0xd2, 0x39, 0x40, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint64_le1(filler_0_16):
    filler_0_16.write_numeric(0, 0x1122334455667788, "uint64_le")
    assert filler_0_16.data == bytearray([0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint64_be1(filler_0_16):
    filler_0_16.write_numeric(0, 0x1122334455667788, "uint64_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_int64_le1(filler_0_16):
    filler_0_16.write_numeric(0, -400000000, "int64_le")
    assert filler_0_16.data == bytearray([0x0, 0x7c, 0x28, 0xe8, 0xff, 0xff, 0xff, 0xff, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_int64_be1(filler_0_16):
    filler_0_16.write_numeric(0, -400000000, "int64_be")
    assert filler_0_16.data == bytearray([0xff, 0xff, 0xff, 0xff, 0xe8, 0x28, 0x7c, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_float32_le1(filler_0_16):
    filler_0_16.write_numeric(0, math.pi, "float32_le")
    assert filler_0_16.data == bytearray([0xdb, 0x0f, 0x49, 0x40, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_float32_be1(filler_0_16):
    filler_0_16.write_numeric(0, math.pi, "float32_be")
    assert filler_0_16.data == bytearray([0x40, 0x49, 0x0f, 0xdb, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_float64_le1(filler_0_16):
    filler_0_16.write_numeric(0, math.pi, "float64_le")
    assert filler_0_16.data == bytearray([0x18, 0x2d, 0x44, 0x54, 0xfb, 0x21, 0x09, 0x40, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_float64_be1(filler_0_16):
    filler_0_16.write_numeric(0, math.pi, "float64_be")
    assert filler_0_16.data == bytearray([0x40, 0x09, 0x21, 0xfb, 0x54, 0x44, 0x2d, 0x18, 0, 0, 0, 0, 0, 0, 0, 0])


