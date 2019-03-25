
import array
import math

import pytest

from objutils.section import Section, filler

def test_default_section():
    section = Section()
    #section = Section2(data=[10, 20, 30, 40])
    assert section.startAddress == 0
    assert section.length == 0
    assert section.data == b''

def test_default_startAddress():
    section = Section(startAddress = 0x10000)
    assert section.startAddress == 0x10000
    assert section.length == 0
    assert section.data == b''

def test_initialize_from_list():
    section = Section(data = [10, 20, 30, 40])
    assert section.startAddress == 0
    assert section.length == 4
    assert section.data == b'\n\x14\x1e('

def test_initialize_from_array1():
    section = Section(data = array.array('B', [10, 20, 30, 40]))
    assert section.startAddress == 0
    assert section.length == 4
    assert section.data == b'\n\x14\x1e('

def test_initialize_from_array2():
    section = Section(data = array.array('H', [0x1010, 0x2020, 0x3030, 0x4040]))
    assert section.startAddress == 0
    assert section.length == 8
    assert section.data == b'\x10\x10  00@@'

def test_initialize_from_range():
    section = Section(data = range(16))
    assert section.startAddress == 0
    assert section.length == 16
    assert section.data == b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'

def test_initialize_from_string():
    section = Section(data = "abcd")
    assert section.startAddress == 0
    assert section.length == 4
    assert section.data == b'abcd'

def test_copy_data_from_other_section():
    data = Section(data = "abcd", startAddress = 0x8000)
    section = Section(data = data)
    assert section.startAddress == 0
    assert section.length == 4
    assert section.data == b'abcd'

def test_copy_really_works():
    section1 = Section(data = range(16), startAddress = 0x8000)
    section2 = Section(data = section1)
    assert section2.startAddress == 0
    assert section2.length == 16
    assert section2.data == b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'
    assert section2.data == section1.data
    section2.writeNumeric(0, 0xff, "uint8_le")
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

@pytest.fixture
def filler_0_16():
    return Section(data = filler(0x00, 16))

def test_write_uint8_le1(filler_0_16):
    filler_0_16.writeNumeric(0, 0xff, "uint8_le")
    assert filler_0_16.data == bytearray([0xff, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint8_be1(filler_0_16):
    filler_0_16.writeNumeric(0, 0xff, "uint8_be")
    assert filler_0_16.data == bytearray([0xff, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint16_le1(filler_0_16):
    filler_0_16.writeNumeric(0, 0x1122, "uint16_le")
    assert filler_0_16.data == bytearray([0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint16_be1(filler_0_16):
    filler_0_16.writeNumeric(0, 0x1122, "uint16_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint32_le1(filler_0_16):
    filler_0_16.writeNumeric(0, 0x11223344, "uint32_le")
    assert filler_0_16.data == bytearray([0x44, 0x33, 0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint32_be1(filler_0_16):
    filler_0_16.writeNumeric(0, 0x11223344, "uint32_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0x33, 0x44, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint64_le1(filler_0_16):
    filler_0_16.writeNumeric(0, 0x1122334455667788, "uint64_le")
    assert filler_0_16.data == bytearray([0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_uint64_be1(filler_0_16):
    filler_0_16.writeNumeric(0, 0x1122334455667788, "uint64_be")
    assert filler_0_16.data == bytearray([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_float32_le1(filler_0_16):
    filler_0_16.writeNumeric(0, math.pi, "float32_le")
    assert filler_0_16.data == bytearray([0xdb, 0x0f, 0x49, 0x40, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_float32_be1(filler_0_16):
    filler_0_16.writeNumeric(0, math.pi, "float32_be")
    assert filler_0_16.data == bytearray([0x40, 0x49, 0x0f, 0xdb, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_float64_le1(filler_0_16):
    filler_0_16.writeNumeric(0, math.pi, "float64_le")
    assert filler_0_16.data == bytearray([0x18, 0x2d, 0x44, 0x54, 0xfb, 0x21, 0x09, 0x40, 0, 0, 0, 0, 0, 0, 0, 0])

def test_write_float64_be1(filler_0_16):
    filler_0_16.writeNumeric(0, math.pi, "float64_be")
    assert filler_0_16.data == bytearray([0x40, 0x09, 0x21, 0xfb, 0x54, 0x44, 0x2d, 0x18, 0, 0, 0, 0, 0, 0, 0, 0])


