#!/usr/bin/env python
"""Tests for the Extended Tektronix (ETek) hex file format.

Coverage:
- loads(): parsing ETek → Image
- dumps(): serialising Image → ETek
- Roundtrip fidelity in both directions (ETek↔SREC)
- Single-byte records at extreme 24-bit addresses
- Checksum mismatch detection
- Record-length mismatch detection
"""

import pytest

from objutils import dumps, loads
from objutils.hexfile import InvalidRecordChecksumError, InvalidRecordLengthError

# ---------------------------------------------------------------------------
# Test vectors
# ---------------------------------------------------------------------------

# 60-byte message split into three 16-byte and one 12-byte data record
# starting at address 0xB000 (24-bit addressing).
ETEK = (
    b"%2A6C200B000576F77212044696420796F7520726561\n"
    b"%2A6DF00B0106C6C7920676F207468726F7567682061\n"
    b"%2A6CE00B0206C6C20746861742074726F75626C6520\n"
    b"%246A700B030746F207265616420746869733F\n"
)

# Equivalent Motorola S-Record representation (used for cross-format checks).
S19 = (
    b"S113B000576F77212044696420796F7520726561D8\n"
    b"S113B0106C6C7920676F207468726F756768206143\n"
    b"S113B0206C6C20746861742074726F75626C652036\n"
    b"S110B030746F207265616420746869733F59\n"
    b"S5030004F8\n"
)

# Single-byte records for boundary / 24-bit address tests.
ETEK_SINGLE_BYTE_LOW = b"%0C628000001AB\n"  # address 0x000001, data 0xAB
ETEK_SINGLE_BYTE_HIGH = b"%0C649FF0000CD\n"  # address 0xFF0000, data 0xCD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _etek_loads(raw: bytes):
    """Load an ETek byte string and return the Image."""
    return loads("etek", raw)


def _srec_loads(raw: bytes):
    """Load an SREC byte string and return the Image."""
    return loads("srec", raw)


# ---------------------------------------------------------------------------
# loads() – parsing
# ---------------------------------------------------------------------------


def test_loads_produces_correct_srec_output():
    """Parsing ETek data produces byte-identical S-Record output."""
    img = _etek_loads(ETEK)
    assert dumps("srec", img, s5record=True) == S19


def test_loads_single_byte_low_address():
    """Single data byte at address 0x000001 is read correctly."""
    img = _etek_loads(ETEK_SINGLE_BYTE_LOW)
    assert img.read(0x000001, 1) == b"\xab"


def test_loads_single_byte_high_address():
    """Single data byte at address 0xFF0000 (max 24-bit) is read correctly."""
    img = _etek_loads(ETEK_SINGLE_BYTE_HIGH)
    assert img.read(0xFF0000, 1) == b"\xcd"


def test_loads_image_min_address():
    """Parsed image starts at the expected minimum address."""
    img = _etek_loads(ETEK)
    first_section = next(iter(img.sections))
    assert first_section.start_address == 0xB000


def test_loads_image_data_length():
    """Parsed image contains the correct number of data bytes (61 = 3×16 + 13)."""
    img = _etek_loads(ETEK)
    total = sum(len(s.data) for s in img.sections)
    assert total == 61


# ---------------------------------------------------------------------------
# dumps() – serialisation
# ---------------------------------------------------------------------------


def test_dumps_produces_correct_etek_output():
    """Serialising an Image loaded from S-Records gives identical ETek bytes."""
    img = _srec_loads(S19)
    assert dumps("etek", img) == bytearray(ETEK)


def test_dumps_single_byte_low_address():
    """A one-byte section at address 0x000001 serialises to the expected record."""
    img = _etek_loads(ETEK_SINGLE_BYTE_LOW)
    assert dumps("etek", img) == bytearray(ETEK_SINGLE_BYTE_LOW)


def test_dumps_single_byte_high_address():
    """A one-byte section at address 0xFF0000 serialises to the expected record."""
    img = _etek_loads(ETEK_SINGLE_BYTE_HIGH)
    assert dumps("etek", img) == bytearray(ETEK_SINGLE_BYTE_HIGH)


# ---------------------------------------------------------------------------
# Roundtrip tests
# ---------------------------------------------------------------------------


def test_roundtrip_etek_to_srec_to_etek():
    """ETek → SREC → ETek roundtrip preserves all data and addresses."""
    img1 = _etek_loads(ETEK)
    srec_data = dumps("srec", img1, s5record=True)
    img2 = _srec_loads(srec_data)
    assert dumps("etek", img2) == bytearray(ETEK)


def test_roundtrip_srec_to_etek_to_srec():
    """SREC → ETek → SREC roundtrip preserves all data and addresses."""
    img1 = _srec_loads(S19)
    etek_data = dumps("etek", img1)
    img2 = _etek_loads(etek_data)
    assert dumps("srec", img2, s5record=True) == S19


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_invalid_checksum_raises():
    """A record with a corrupted checksum raises InvalidRecordChecksumError."""
    # Flip one nibble in the CC field (chars 4-5 of the record).
    bad = b"%2A6FF00B000576F77212044696420796F7520726561\n"
    with pytest.raises(InvalidRecordChecksumError):
        _etek_loads(bad)


def test_invalid_length_raises():
    """A record with a wrong LL field raises InvalidRecordLengthError."""
    # Change LL from 2A to 2C (claims 19 data bytes but only 16 are present).
    bad = b"%2C6C200B000576F77212044696420796F7520726561\n"
    with pytest.raises(InvalidRecordLengthError):
        _etek_loads(bad)
