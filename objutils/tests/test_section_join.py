import pytest

from objutils.section import Section, join_sections


def test_join_sections_collapses_identical_duplicates_and_contiguous_data() -> None:
    sections = [
        Section(0x1000, b"AAAA"),
        Section(0x1000, b"AAAA"),
        Section(0x1004, b"BBBB"),
        Section(0x1004, b"BBBB"),
    ]

    joined = join_sections(sections)

    assert len(joined) == 1
    assert joined[0].start_address == 0x1000
    assert joined[0].data == b"AAAABBBB"


def test_join_sections_merges_contained_identical_section() -> None:
    sections = [
        Section(0x3001, b"\x20\x30"),
        Section(0x3000, b"\x10\x20\x30\x40\x50"),
    ]

    joined = join_sections(sections)

    assert len(joined) == 1
    assert joined[0].start_address == 0x3000
    assert joined[0].data == b"\x10\x20\x30\x40\x50"


def test_join_sections_merges_suffix_overlap_from_unsorted_input() -> None:
    sections = [
        Section(0x2002, b"\x33\x44\x55\x66"),
        Section(0x2000, b"\x11\x22\x33\x44"),
    ]

    joined = join_sections(sections)

    assert len(joined) == 1
    assert joined[0].start_address == 0x2000
    assert joined[0].data == b"\x11\x22\x33\x44\x55\x66"


def test_join_sections_merges_transitive_overlap_chain() -> None:
    sections = [
        Section(0x1000, b"ABCD"),
        Section(0x1002, b"CD12"),
        Section(0x1004, b"1234"),
    ]

    joined = join_sections(sections)

    assert len(joined) == 1
    assert joined[0].start_address == 0x1000
    assert joined[0].data == b"ABCD1234"


def test_join_sections_keeps_conflict_split_but_merges_followup() -> None:
    sections = [
        Section(0x1000, b"\x01\x02\x03\x04"),
        Section(0x1002, b"\x09\x09\x05\x06"),
        Section(0x1006, b"\x07\x08"),
    ]

    joined = join_sections(sections)

    assert len(joined) == 2
    assert joined[0].start_address == 0x1000
    assert joined[0].data == b"\x01\x02\x03\x04"
    assert joined[1].start_address == 0x1002
    assert joined[1].data == b"\x09\x09\x05\x06\x07\x08"


def test_join_sections_rejects_non_section_entries() -> None:
    with pytest.raises(TypeError):
        join_sections([Section(0x1000, b"A"), "not-a-section"])  # type: ignore[list-item]
