"""Unit-Tests für ASAM ALTERNATE_WITH_X und ALTERNATE_WITH_Y index_mode.

Spezifikation
-------------
ALTERNATE_WITH_X (für Kennfelder / maps):
    Für jede X-Spalte i wird zunächst der X-Achsenwert, dann alle Y-Werte
    dieser Spalte abgespeichert::

        [x[0], f(x0,y0), f(x0,y1), …, x[1], f(x1,y0), f(x1,y1), …]

ALTERNATE_WITH_Y (für Kennfelder / maps):
    Für jede Y-Zeile j wird zunächst der Y-Achsenwert, dann alle X-Werte
    dieser Zeile abgespeichert::

        [y[0], f(x0,y0), f(x1,y0), …, y[1], f(x0,y1), f(x1,y1), …]

``read_asam_ndarray`` gibt für diese Modi ein :class:`AlternateArrayResult`-
Named-Tuple ``(values, axis)`` zurück; ``write_asam_ndarray`` erwartet die
Achsenwerte als optionalen ``x_axis``- bzw. ``y_axis``-Keyword-Parameter.
"""

import pytest

from objutils.section import AlternateArrayResult, Section

try:
    import numpy as np

    NUMPY_SUPPORT = True
except ImportError:
    NUMPY_SUPPORT = False


# ---------------------------------------------------------------------------
# Hilfsdaten
# ---------------------------------------------------------------------------

# Beispiel-Kennfeld  (X-Dimension = 3, Y-Dimension = 4)
# Numpy-Shape: (4, 3)  –  4 Zeilen (Y), 3 Spalten (X)
#
#        x=0  x=1  x=2
# y=0:   11   21   31
# y=1:   12   22   32
# y=2:   13   23   33
# y=3:   14   24   34

VALUES_2D = [
    [11, 21, 31],
    [12, 22, 32],
    [13, 23, 33],
    [14, 24, 34],
]

X_AXIS_3 = [100, 200, 300]  # X-Achse, 3 Werte
Y_AXIS_4 = [10, 20, 30, 40]  # Y-Achse, 4 Werte


# ---------------------------------------------------------------------------
# ALTERNATE_WITH_X – Speicherlayout
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_memory_layout_ubyte():
    """ALTERNATE_WITH_X: Rohspeicher enthält x[i] gefolgt von den Y-Werten der Spalte."""
    arr = np.array(VALUES_2D, dtype=np.uint8)  # shape (4, 3)
    # UBYTE: max 255, daher Achsenwerte innerhalb [0, 255]
    x_axis = np.array([10, 20, 30], dtype=np.uint8)

    # Erwartetes Speicherlayout:
    #   x[0]=10, col0=[11,12,13,14], x[1]=20, col1=[21,22,23,24], x[2]=30, col2=[31,32,33,34]
    expected = [
        10,
        11,
        12,
        13,
        14,
        20,
        21,
        22,
        23,
        24,
        30,
        31,
        32,
        33,
        34,
    ]

    total_bytes = 3 * (1 + 4)  # num_x * (axis_byte + num_y * data_byte)
    sec = Section(start_address=0x1000, data=bytearray(total_bytes + 16))
    sec.write_asam_ndarray(0x1000, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

    assert list(sec.read(0x1000, total_bytes)) == expected


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_memory_layout_uword():
    """ALTERNATE_WITH_X mit UWORD (16-Bit LE): korrekte Byte-Reihenfolge."""
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)  # shape (2, 3)
    x_axis = np.array([100, 200, 300], dtype=np.uint16)

    # Erwartetes Layout (LE):
    # x[0]=100 → 0x64 0x00
    # col0=[1,4] → 0x01 0x00  0x04 0x00
    # x[1]=200 → 0xC8 0x00
    # col1=[2,5] → 0x02 0x00  0x05 0x00
    # x[2]=300 → 0x2C 0x01
    # col2=[3,6] → 0x03 0x00  0x06 0x00
    expected = [
        0x64,
        0x00,  # x[0]=100
        0x01,
        0x00,  # f(0,0)=1
        0x04,
        0x00,  # f(0,1)=4
        0xC8,
        0x00,  # x[1]=200
        0x02,
        0x00,  # f(1,0)=2
        0x05,
        0x00,  # f(1,1)=5
        0x2C,
        0x01,  # x[2]=300
        0x03,
        0x00,  # f(2,0)=3
        0x06,
        0x00,  # f(2,1)=6
    ]
    total_bytes = 3 * (2 + 2 * 2)  # num_x * (axis_bytes + num_y * element_bytes)
    sec = Section(start_address=0, data=bytearray(total_bytes + 16))
    sec.write_asam_ndarray(0, arr, "UWORD", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

    assert list(sec.read(0, total_bytes)) == expected


# ---------------------------------------------------------------------------
# ALTERNATE_WITH_X – Roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_roundtrip_ubyte():
    """Write → Read Roundtrip für ALTERNATE_WITH_X (UBYTE)."""
    arr = np.array(VALUES_2D, dtype=np.uint8)  # shape (4, 3)
    x_axis = np.array([10, 20, 30], dtype=np.uint8)

    total_bytes = 3 * (1 + 4)
    sec = Section(start_address=0x2000, data=bytearray(total_bytes + 32))
    sec.write_asam_ndarray(0x2000, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

    # ASAM shape: (X=3, Y=4)
    result = sec.read_asam_ndarray(0x2000, 0, "UBYTE", shape=(3, 4), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")

    assert isinstance(result, AlternateArrayResult)
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, x_axis)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_roundtrip_uword():
    """Write → Read Roundtrip für ALTERNATE_WITH_X (UWORD, LE)."""
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)  # shape (2, 3)
    x_axis = np.array([100, 200, 300], dtype=np.uint16)

    total_bytes = 3 * (2 + 2 * 2)
    sec = Section(start_address=0, data=bytearray(total_bytes + 16))
    sec.write_asam_ndarray(0, arr, "UWORD", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

    result = sec.read_asam_ndarray(0, 0, "UWORD", shape=(3, 2), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")

    assert isinstance(result, AlternateArrayResult)
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, x_axis)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_result_shape():
    """AlternateArrayResult hat korrekte Shapes."""
    arr = np.zeros((4, 3), dtype=np.uint8)  # Y=4, X=3
    x_axis = np.array([1, 2, 3], dtype=np.uint8)

    total_bytes = 3 * (1 + 4)
    sec = Section(start_address=0, data=bytearray(total_bytes + 8))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

    result = sec.read_asam_ndarray(0, 0, "UBYTE", shape=(3, 4), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")

    assert result.values.shape == (4, 3)  # numpy: (Y, X)
    assert result.axis.shape == (3,)  # X-Achse


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_no_x_axis_written():
    """Wenn kein x_axis übergeben wird, werden nur Werte ohne Achsenstubs geschrieben."""
    arr = np.array([[1, 2], [3, 4]], dtype=np.uint8)  # Y=2, X=2

    # Ohne x_axis: jede Spalte direkt ohne vorangestellten Achsenwert
    # Layout: col0=[1,3], col1=[2,4]  → [1, 3, 2, 4]
    expected = [1, 3, 2, 4]
    sec = Section(start_address=0, data=bytearray(16))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")

    assert list(sec.read(0, 4)) == expected


# ---------------------------------------------------------------------------
# ALTERNATE_WITH_Y – Speicherlayout
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_memory_layout_ubyte():
    """ALTERNATE_WITH_Y: Rohspeicher enthält y[j] gefolgt von den X-Werten der Zeile."""
    arr = np.array(VALUES_2D, dtype=np.uint8)  # shape (4, 3)
    y_axis = np.array(Y_AXIS_4, dtype=np.uint8)

    # Erwartetes Speicherlayout:
    #   y[0]=10, row0=[11,21,31], y[1]=20, row1=[12,22,32], y[2]=30, row2=[13,23,33], y[3]=40, row3=[14,24,34]
    expected = [
        10,
        11,
        21,
        31,
        20,
        12,
        22,
        32,
        30,
        13,
        23,
        33,
        40,
        14,
        24,
        34,
    ]
    total_bytes = 4 * (1 + 3)  # num_y * (axis_byte + num_x * data_byte)
    sec = Section(start_address=0x1000, data=bytearray(total_bytes + 16))
    sec.write_asam_ndarray(0x1000, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

    assert list(sec.read(0x1000, total_bytes)) == expected


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_memory_layout_uword():
    """ALTERNATE_WITH_Y mit UWORD (16-Bit LE): korrekte Byte-Reihenfolge."""
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)  # shape (2, 3)  Y=2, X=3
    y_axis = np.array([100, 200], dtype=np.uint16)

    # Erwartetes Layout (LE):
    # y[0]=100 → 0x64 0x00
    # row0=[1,2,3] → 0x01 0x00  0x02 0x00  0x03 0x00
    # y[1]=200 → 0xC8 0x00
    # row1=[4,5,6] → 0x04 0x00  0x05 0x00  0x06 0x00
    expected = [
        0x64,
        0x00,  # y[0]=100
        0x01,
        0x00,  # f(0,0)=1
        0x02,
        0x00,  # f(1,0)=2
        0x03,
        0x00,  # f(2,0)=3
        0xC8,
        0x00,  # y[1]=200
        0x04,
        0x00,  # f(0,1)=4
        0x05,
        0x00,  # f(1,1)=5
        0x06,
        0x00,  # f(2,1)=6
    ]
    total_bytes = 2 * (2 + 3 * 2)  # num_y * (axis_bytes + num_x * element_bytes)
    sec = Section(start_address=0, data=bytearray(total_bytes + 16))
    sec.write_asam_ndarray(0, arr, "UWORD", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

    assert list(sec.read(0, total_bytes)) == expected


# ---------------------------------------------------------------------------
# ALTERNATE_WITH_Y – Roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_roundtrip_ubyte():
    """Write → Read Roundtrip für ALTERNATE_WITH_Y (UBYTE)."""
    arr = np.array(VALUES_2D, dtype=np.uint8)  # shape (4, 3)  Y=4, X=3
    y_axis = np.array([10, 20, 30, 40], dtype=np.uint8)

    total_bytes = 4 * (1 + 3)
    sec = Section(start_address=0x3000, data=bytearray(total_bytes + 32))
    sec.write_asam_ndarray(0x3000, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

    # ASAM shape: (X=3, Y=4)
    result = sec.read_asam_ndarray(0x3000, 0, "UBYTE", shape=(3, 4), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y")

    assert isinstance(result, AlternateArrayResult)
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, y_axis)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_roundtrip_uword():
    """Write → Read Roundtrip für ALTERNATE_WITH_Y (UWORD, LE)."""
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)  # Y=2, X=3
    y_axis = np.array([100, 200], dtype=np.uint16)

    total_bytes = 2 * (2 + 3 * 2)
    sec = Section(start_address=0, data=bytearray(total_bytes + 16))
    sec.write_asam_ndarray(0, arr, "UWORD", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

    result = sec.read_asam_ndarray(0, 0, "UWORD", shape=(3, 2), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y")

    assert isinstance(result, AlternateArrayResult)
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, y_axis)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_result_shape():
    """AlternateArrayResult hat korrekte Shapes für ALTERNATE_WITH_Y."""
    arr = np.zeros((4, 3), dtype=np.uint8)  # Y=4, X=3
    y_axis = np.array([1, 2, 3, 4], dtype=np.uint8)

    total_bytes = 4 * (1 + 3)
    sec = Section(start_address=0, data=bytearray(total_bytes + 8))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

    result = sec.read_asam_ndarray(0, 0, "UBYTE", shape=(3, 4), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y")

    assert result.values.shape == (4, 3)  # numpy: (Y, X)
    assert result.axis.shape == (4,)  # Y-Achse


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_no_y_axis_written():
    """Wenn kein y_axis übergeben wird, werden nur Werte ohne Achsenstubs geschrieben."""
    arr = np.array([[1, 2], [3, 4]], dtype=np.uint8)  # Y=2, X=2

    # Ohne y_axis: jede Zeile direkt ohne vorangestellten Achsenwert
    # Layout: row0=[1,2], row1=[3,4]  → [1, 2, 3, 4]
    expected = [1, 2, 3, 4]
    sec = Section(start_address=0, data=bytearray(16))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y")

    assert list(sec.read(0, 4)) == expected


# ---------------------------------------------------------------------------
# Symmetrie: ALTERNATE_WITH_X vs ALTERNATE_WITH_Y
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_x_y_produce_different_layouts():
    """ALTERNATE_WITH_X und ALTERNATE_WITH_Y erzeugen unterschiedliche Speicher-Layouts."""
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)  # Y=2, X=3
    x_axis = np.array([10, 20, 30], dtype=np.uint8)
    y_axis = np.array([100, 200], dtype=np.uint8)

    sec_x = Section(start_address=0, data=bytearray(32))
    sec_y = Section(start_address=0, data=bytearray(32))

    sec_x.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)
    sec_y.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

    total_x = 3 * (1 + 2)
    total_y = 2 * (1 + 3)

    raw_x = list(sec_x.read(0, total_x))
    raw_y = list(sec_y.read(0, total_y))

    assert raw_x != raw_y  # Layouts müssen verschieden sein


# ---------------------------------------------------------------------------
# Fehlerbehandlung
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_requires_2d():
    """ALTERNATE_WITH_X mit 1-D Array: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(32))
    arr = np.array([1, 2, 3], dtype=np.uint8)
    with pytest.raises(ValueError, match="2-D"):
        sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_requires_2d():
    """ALTERNATE_WITH_Y mit 1-D Array: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(32))
    arr = np.array([1, 2, 3], dtype=np.uint8)
    with pytest.raises(ValueError, match="2-D"):
        sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y")


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_wrong_axis_length():
    """ALTERNATE_WITH_X mit x_axis falscher Länge: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(64))
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)  # X=3
    x_axis = np.array([10, 20], dtype=np.uint8)  # Länge 2 ≠ X=3
    with pytest.raises(ValueError, match="x_axis length"):
        sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_wrong_axis_length():
    """ALTERNATE_WITH_Y mit y_axis falscher Länge: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(64))
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)  # Y=2
    y_axis = np.array([10, 20, 30], dtype=np.uint8)  # Länge 3 ≠ Y=2
    with pytest.raises(ValueError, match="y_axis length"):
        sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_read_requires_2d_shape():
    """read_asam_ndarray mit ALTERNATE_WITH_X ohne 2-D shape: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(32))
    with pytest.raises(ValueError, match="2-D shape"):
        sec.read_asam_ndarray(0, 0, "UBYTE", shape=(3,), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_read_requires_2d_shape():
    """read_asam_ndarray mit ALTERNATE_WITH_Y ohne 2-D shape: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(32))
    with pytest.raises(ValueError, match="2-D shape"):
        sec.read_asam_ndarray(0, 0, "UBYTE", shape=(3,), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y")


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_read_no_shape():
    """read_asam_ndarray mit ALTERNATE_WITH_X ohne shape: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(32))
    with pytest.raises(ValueError):
        sec.read_asam_ndarray(0, 0, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_invalid_index_mode_write():
    """Unbekannter index_mode beim Schreiben: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(32))
    arr = np.array([[1, 2]], dtype=np.uint8)
    with pytest.raises(ValueError):
        sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_CURVES")


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_invalid_index_mode_read():
    """Unbekannter index_mode beim Lesen: ValueError erwartet."""
    sec = Section(start_address=0, data=bytearray(32))
    with pytest.raises(ValueError):
        sec.read_asam_ndarray(0, 4, "UBYTE", shape=(2, 2), byte_order="MSB_LAST", index_mode="ALTERNATE_CURVES")


# ---------------------------------------------------------------------------
# AlternateArrayResult Named-Tuple Interface
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_array_result_named_tuple_access():
    """AlternateArrayResult: Zugriff über Attributname und Index."""
    arr = np.array([[1, 2], [3, 4]], dtype=np.uint8)
    x_axis = np.array([10, 20], dtype=np.uint8)

    total_bytes = 2 * (1 + 2)
    sec = Section(start_address=0, data=bytearray(total_bytes + 8))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

    result = sec.read_asam_ndarray(0, 0, "UBYTE", shape=(2, 2), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")

    # Zugriff über Attributnamen
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, x_axis)

    # Zugriff über Index
    assert np.array_equal(result[0], arr)
    assert np.array_equal(result[1], x_axis)

    # Unpacking
    values, axis = result
    assert np.array_equal(values, arr)
    assert np.array_equal(axis, x_axis)


# ---------------------------------------------------------------------------
# Großes Beispiel aus der ASAM-Spezifikation (VAL_BLK MATRIX_DIM 5 4)
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_spec_example():
    """ALTERNATE_WITH_X: großes Kennfeld aus der ASAM-Spezifikation.

    Wertematrix (5 Spalten, 4 Zeilen):
        11 21 31 41 51
        12 22 32 42 52
        13 23 33 43 53
        14 24 34 44 54

    X-Achse: [1, 2, 3, 4, 5] (5 Werte)

    Erwartetes Speicherlayout:
        x[0]=1, 11, 12, 13, 14,
        x[1]=2, 21, 22, 23, 24,
        x[2]=3, 31, 32, 33, 34,
        x[3]=4, 41, 42, 43, 44,
        x[4]=5, 51, 52, 53, 54
    """
    arr = np.array(
        [
            [11, 21, 31, 41, 51],
            [12, 22, 32, 42, 52],
            [13, 23, 33, 43, 53],
            [14, 24, 34, 44, 54],
        ],
        dtype=np.uint8,
    )  # numpy shape: (4 rows=Y, 5 cols=X)
    x_axis = np.array([1, 2, 3, 4, 5], dtype=np.uint8)

    expected_flat = [
        1,
        11,
        12,
        13,
        14,
        2,
        21,
        22,
        23,
        24,
        3,
        31,
        32,
        33,
        34,
        4,
        41,
        42,
        43,
        44,
        5,
        51,
        52,
        53,
        54,
    ]

    total_bytes = 5 * (1 + 4)
    sec = Section(start_address=0, data=bytearray(total_bytes + 16))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

    assert list(sec.read(0, total_bytes)) == expected_flat

    # Roundtrip
    result = sec.read_asam_ndarray(0, 0, "UBYTE", shape=(5, 4), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_X")
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, x_axis)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_spec_example():
    """ALTERNATE_WITH_Y: großes Kennfeld aus der ASAM-Spezifikation.

    Wertematrix (5 Spalten, 4 Zeilen):
        11 21 31 41 51
        12 22 32 42 52
        13 23 33 43 53
        14 24 34 44 54

    Y-Achse: [1, 2, 3, 4] (4 Werte)

    Erwartetes Speicherlayout:
        y[0]=1, 11, 21, 31, 41, 51,
        y[1]=2, 12, 22, 32, 42, 52,
        y[2]=3, 13, 23, 33, 43, 53,
        y[3]=4, 14, 24, 34, 44, 54
    """
    arr = np.array(
        [
            [11, 21, 31, 41, 51],
            [12, 22, 32, 42, 52],
            [13, 23, 33, 43, 53],
            [14, 24, 34, 44, 54],
        ],
        dtype=np.uint8,
    )  # numpy shape: (4 rows=Y, 5 cols=X)
    y_axis = np.array([1, 2, 3, 4], dtype=np.uint8)

    expected_flat = [
        1,
        11,
        21,
        31,
        41,
        51,
        2,
        12,
        22,
        32,
        42,
        52,
        3,
        13,
        23,
        33,
        43,
        53,
        4,
        14,
        24,
        34,
        44,
        54,
    ]

    total_bytes = 4 * (1 + 5)
    sec = Section(start_address=0, data=bytearray(total_bytes + 16))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

    assert list(sec.read(0, total_bytes)) == expected_flat

    # Roundtrip
    result = sec.read_asam_ndarray(0, 0, "UBYTE", shape=(5, 4), byte_order="MSB_LAST", index_mode="ALTERNATE_WITH_Y")
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, y_axis)


# ---------------------------------------------------------------------------
# BE (Big-Endian) Byte-Reihenfolge
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_x_big_endian():
    """ALTERNATE_WITH_X mit BE (MSB_FIRST): korrekte Byte-Reihenfolge."""
    arr = np.array([[0x0102, 0x0304], [0x0506, 0x0708]], dtype=np.uint16)  # Y=2, X=2
    x_axis = np.array([0x0A0B, 0x0C0D], dtype=np.uint16)

    # BE Layout:
    # x[0]=0x0A0B → 0x0A 0x0B
    # col0=[0x0102, 0x0506] → 0x01 0x02  0x05 0x06
    # x[1]=0x0C0D → 0x0C 0x0D
    # col1=[0x0304, 0x0708] → 0x03 0x04  0x07 0x08
    expected = [0x0A, 0x0B, 0x01, 0x02, 0x05, 0x06, 0x0C, 0x0D, 0x03, 0x04, 0x07, 0x08]

    total_bytes = 2 * (2 + 2 * 2)
    sec = Section(start_address=0, data=bytearray(total_bytes + 8))
    sec.write_asam_ndarray(0, arr, "UWORD", byte_order="MSB_FIRST", index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

    assert list(sec.read(0, total_bytes)) == expected

    result = sec.read_asam_ndarray(0, 0, "UWORD", shape=(2, 2), byte_order="MSB_FIRST", index_mode="ALTERNATE_WITH_X")
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, x_axis)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_alternate_with_y_big_endian():
    """ALTERNATE_WITH_Y mit BE (MSB_FIRST): korrekte Byte-Reihenfolge."""
    arr = np.array([[0x0102, 0x0304], [0x0506, 0x0708]], dtype=np.uint16)  # Y=2, X=2
    y_axis = np.array([0x0A0B, 0x0C0D], dtype=np.uint16)

    # BE Layout:
    # y[0]=0x0A0B → 0x0A 0x0B
    # row0=[0x0102, 0x0304] → 0x01 0x02  0x03 0x04
    # y[1]=0x0C0D → 0x0C 0x0D
    # row1=[0x0506, 0x0708] → 0x05 0x06  0x07 0x08
    expected = [0x0A, 0x0B, 0x01, 0x02, 0x03, 0x04, 0x0C, 0x0D, 0x05, 0x06, 0x07, 0x08]

    total_bytes = 2 * (2 + 2 * 2)
    sec = Section(start_address=0, data=bytearray(total_bytes + 8))
    sec.write_asam_ndarray(0, arr, "UWORD", byte_order="MSB_FIRST", index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

    assert list(sec.read(0, total_bytes)) == expected

    result = sec.read_asam_ndarray(0, 0, "UWORD", shape=(2, 2), byte_order="MSB_FIRST", index_mode="ALTERNATE_WITH_Y")
    assert np.array_equal(result.values, arr)
    assert np.array_equal(result.axis, y_axis)


# ---------------------------------------------------------------------------
# Kompatibilität: ROW_DIR und COLUMN_DIR weiterhin unverändert
# ---------------------------------------------------------------------------


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_row_dir_still_works():
    """ROW_DIR ist durch die neuen Modi nicht beeinträchtigt."""
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)
    sec = Section(start_address=0, data=bytearray(16))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="ROW_DIR")
    result = sec.read_asam_ndarray(0, 6, "UBYTE", shape=(3, 2), byte_order="MSB_LAST", index_mode="ROW_DIR")
    assert np.array_equal(result, arr)


@pytest.mark.skipif("NUMPY_SUPPORT == False")
def test_column_dir_still_works():
    """COLUMN_DIR ist durch die neuen Modi nicht beeinträchtigt."""
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)
    sec = Section(start_address=0, data=bytearray(16))
    sec.write_asam_ndarray(0, arr, "UBYTE", byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    result = sec.read_asam_ndarray(0, 6, "UBYTE", shape=(3, 2), byte_order="MSB_LAST", index_mode="COLUMN_DIR")
    assert np.array_equal(result, arr)
