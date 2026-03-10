#!/usr/bin/env python
"""Test script to verify join_sections() functionality."""

from objutils import Section, Image
from objutils.section import join_sections


def test_consecutive_sections():
    """Test joining consecutive sections."""
    print("Test 1: Consecutive sections")
    print("-" * 80)

    sections = [
        Section(0x1000, b"Hello"),
        Section(0x1005, b" "),
        Section(0x1006, b"World"),
    ]

    print("Before join:")
    for idx, sec in enumerate(sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    joined = join_sections(sections)

    print("\nAfter join:")
    for idx, sec in enumerate(joined):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    assert len(joined) == 1, f"Expected 1 section, got {len(joined)}"
    assert joined[0].start_address == 0x1000, f"Expected start_address 0x1000, got 0x{joined[0].start_address:04x}"
    assert joined[0].length == 11, f"Expected length 11, got {joined[0].length}"
    assert joined[0].data == b"Hello World", f"Expected b'Hello World', got {joined[0].data}"
    print("✓ PASSED\n")


def test_non_consecutive_sections():
    """Test that non-consecutive sections remain separate."""
    print("Test 2: Non-consecutive sections (with gap)")
    print("-" * 80)

    sections = [
        Section(0x1000, b"Hello"),
        Section(0x1005, b" "),
        Section(0x2000, b"World"),  # Gap before this
    ]

    print("Before join:")
    for idx, sec in enumerate(sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    joined = join_sections(sections)

    print("\nAfter join:")
    for idx, sec in enumerate(joined):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    assert len(joined) == 2, f"Expected 2 sections, got {len(joined)}"
    assert joined[0].start_address == 0x1000
    assert joined[0].length == 6
    assert joined[0].data == b"Hello "
    assert joined[1].start_address == 0x2000
    assert joined[1].length == 5
    assert joined[1].data == b"World"
    print("✓ PASSED\n")


def test_unsorted_input():
    """Test that unsorted input is sorted correctly."""
    print("Test 3: Unsorted input sections")
    print("-" * 80)

    sections = [
        Section(0x2000, b"World"),
        Section(0x1000, b"Hello"),
        Section(0x1005, b" "),
    ]

    print("Before join (unsorted):")
    for idx, sec in enumerate(sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    joined = join_sections(sections)

    print("\nAfter join (sorted and joined):")
    for idx, sec in enumerate(joined):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    assert len(joined) == 2, f"Expected 2 sections, got {len(joined)}"
    assert joined[0].start_address == 0x1000
    assert joined[1].start_address == 0x2000
    print("✓ PASSED\n")


def test_image_with_join():
    """Test Image class with join=True."""
    print("Test 4: Image class with join=True")
    print("-" * 80)

    sections = [
        Section(0x1000, b"AAA"),
        Section(0x1003, b"BBB"),
        Section(0x1006, b"CCC"),
        Section(0x2000, b"DDD"),
    ]

    print("Before join:")
    for idx, sec in enumerate(sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    img = Image(sections, join=True)

    print("\nAfter Image(join=True):")
    for idx, sec in enumerate(img.sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    assert len(img.sections) == 2, f"Expected 2 sections, got {len(img.sections)}"
    assert img.sections[0].start_address == 0x1000
    assert img.sections[0].length == 9
    assert img.sections[0].data == b"AAABBBCCC"
    assert img.sections[1].start_address == 0x2000
    assert img.sections[1].length == 3
    assert img.sections[1].data == b"DDD"
    print("✓ PASSED\n")


def test_image_without_join():
    """Test Image class with join=False."""
    print("Test 5: Image class with join=False")
    print("-" * 80)

    sections = [
        Section(0x1000, b"AAA"),
        Section(0x1003, b"BBB"),
    ]

    print("Before Image:")
    for idx, sec in enumerate(sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    img = Image(sections, join=False)

    print("\nAfter Image(join=False):")
    for idx, sec in enumerate(img.sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    assert len(img.sections) == 2, f"Expected 2 sections, got {len(img.sections)}"
    print("✓ PASSED\n")


def test_join_sections_method():
    """Test Image.join_sections() method."""
    print("Test 6: Image.join_sections() method")
    print("-" * 80)

    sections = [
        Section(0x1000, b"AAA"),
        Section(0x1003, b"BBB"),
        Section(0x2000, b"CCC"),
    ]

    img = Image(sections, join=False)

    print("Before join_sections():")
    for idx, sec in enumerate(img.sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    img.join_sections()

    print("\nAfter join_sections():")
    for idx, sec in enumerate(img.sections):
        print(f"  Section {idx}: Address=0x{sec.start_address:04x}, Length={sec.length}, Data={sec.data}")

    assert len(img.sections) == 2, f"Expected 2 sections, got {len(img.sections)}"
    assert img.sections[0].start_address == 0x1000
    assert img.sections[0].length == 6
    assert img.sections[0].data == b"AAABBB"
    assert img.sections[1].start_address == 0x2000
    print("✓ PASSED\n")


def test_empty_list():
    """Test with empty list."""
    print("Test 7: Empty section list")
    print("-" * 80)

    sections = []
    joined = join_sections(sections)

    print(f"Result: {joined}")
    assert joined == [], f"Expected empty list, got {joined}"
    print("✓ PASSED\n")


def test_single_section():
    """Test with single section."""
    print("Test 8: Single section")
    print("-" * 80)

    sections = [Section(0x1000, b"Hello")]
    joined = join_sections(sections)

    print(f"Before: {sections[0]}")
    print(f"After: {joined[0]}")
    assert len(joined) == 1
    assert joined[0].start_address == 0x1000
    assert joined[0].data == b"Hello"
    print("✓ PASSED\n")


def test_address_and_length_correctness():
    """Test that address and length are calculated correctly."""
    print("Test 9: Address and length correctness")
    print("-" * 80)

    sections = [
        Section(0x0000, b"\x01\x02\x03"),
        Section(0x0003, b"\x04\x05"),
        Section(0x0005, b"\x06\x07\x08\x09"),
        Section(0x1000, b"\x0A"),
    ]

    print("Before join:")
    for idx, sec in enumerate(sections):
        end_addr = sec.start_address + sec.length
        print(f"  Section {idx}: 0x{sec.start_address:04x}-0x{end_addr:04x}, Length={sec.length}")

    joined = join_sections(sections)

    print("\nAfter join:")
    for idx, sec in enumerate(joined):
        end_addr = sec.start_address + sec.length
        print(f"  Section {idx}: 0x{sec.start_address:04x}-0x{end_addr:04x}, Length={sec.length}, Data={sec.data.hex()}")

    assert len(joined) == 2
    # First merged section: 0x0000 to 0x0009
    assert joined[0].start_address == 0x0000
    assert joined[0].length == 9
    assert joined[0].data == b"\x01\x02\x03\x04\x05\x06\x07\x08\x09"
    # Second section: 0x1000 to 0x1001
    assert joined[1].start_address == 0x1000
    assert joined[1].length == 1
    assert joined[1].data == b"\x0A"
    print("✓ PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING join_sections() FUNCTIONALITY")
    print("=" * 80 + "\n")

    try:
        test_consecutive_sections()
        test_non_consecutive_sections()
        test_unsorted_input()
        test_image_with_join()
        test_image_without_join()
        test_join_sections_method()
        test_empty_list()
        test_single_section()
        test_address_and_length_correctness()

        print("=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

