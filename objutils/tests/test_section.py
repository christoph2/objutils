
import array

import pytest

from objutils.section import Section

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


def test_initialize_from_string():
    section = Section(data = "abcd")
    assert section.startAddress == 0
    assert section.length == 4
    assert section.data == b'abcd'


def test_copy_data_from_other_section():
    data=Section(data = "abcd", startAddress = 0x8000)
    section = Section(data = data)
    assert section.startAddress == 0
    assert section.length == 4
    assert section.data == b'abcd'

def test_single_int_not_permitted():
    with pytest.raises(ValueError):
        Section(data = 42)

