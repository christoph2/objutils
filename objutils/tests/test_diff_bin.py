import copy
import string

from objutils.utils.diff import BinDiff, diff_bin


def test_modify1():
    b0 = bytearray(range(256))
    b1 = copy.copy(b0)
    b1[126] = 11
    b1[127] = 12
    b1[128] = 13
    b1[136] = 14
    res = diff_bin(b0, b1)
    assert res == [
        BinDiff(type="M", offset=126, a=bytearray(b"~\x7f\x80"), b=bytearray(b"\x0b\x0c\r")),
        BinDiff(type="M", offset=136, a=bytearray(b"\x88"), b=bytearray(b"\x0e")),
    ]


def test_modify2():
    let0 = bytearray(string.ascii_letters, "ascii")
    let1 = copy.copy(let0)
    let1[20:25] = b"hello"
    let1[45:50] = b"world"
    res = diff_bin(let0, let1)
    assert res == [
        BinDiff(type="M", offset=20, a=bytearray(b"uvwxy"), b=bytearray(b"hello")),
        BinDiff(type="M", offset=45, a=bytearray(b"TUVWX"), b=bytearray(b"world")),
    ]


def test_append():
    h0 = bytes("hello", "ascii")
    h1 = bytes("hello world", "ascii")
    res = diff_bin(h0, h1)
    assert res == [BinDiff(type="A", offset=5, a=None, b=b" world")]


def test_delete():
    h1 = bytes("hello", "ascii")
    h0 = bytes("hello world", "ascii")
    res = diff_bin(h0, h1)
    assert res == [BinDiff(type="D", offset=5, a=b" world", b=None)]
