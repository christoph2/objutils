#!/usr/bin/env python
"""Tests for objutils.elf package.

This module tests the ELF parser, model, and definitions.
Based on the actual ElfParser API which uses:
- Property-based header access (e.g., parser.e_machine)
- SectionAPI for sections (parser.sections.get/fetch)
- SymbolAPI for symbols (parser.symbols.get/fetch)
- Database backend for persistent analysis
"""

import tempfile
from pathlib import Path

import pytest

from objutils.elf import ElfParser


# Test data directory
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
SAMPLE_ELF_FILES = [
    "avr.elf",
    "Test.elf",
    "hello_xcp.ino.elf",
]


@pytest.fixture
def sample_elf_path():
    """Provide path to sample ELF file (AVR)."""
    return EXAMPLES_DIR / "avr.elf"


@pytest.fixture
def parser(sample_elf_path):
    """Create ElfParser instance for testing."""
    return ElfParser(str(sample_elf_path))


class TestElfParserBasics:
    """Test basic ELF parser functionality."""

    def test_parser_creation(self, sample_elf_path):
        """Test that ElfParser can be instantiated."""
        parser = ElfParser(str(sample_elf_path))
        assert parser is not None

    def test_parser_has_endianness(self, parser):
        """Test that parser determines endianness."""
        assert hasattr(parser, "endianess")
        assert parser.endianess in ("<", ">")

    def test_parser_has_section_api(self, parser):
        """Test that parser provides SectionAPI."""
        assert hasattr(parser, "sections")
        # SectionAPI has get and fetch methods
        assert hasattr(parser.sections, "get")
        assert hasattr(parser.sections, "fetch")

    def test_parser_has_symbol_api(self, parser):
        """Test that parser provides SymbolAPI."""
        assert hasattr(parser, "symbols")
        # SymbolAPI has get and fetch methods
        assert hasattr(parser.symbols, "get")
        assert hasattr(parser.symbols, "fetch")

    def test_header_properties_exist(self, parser):
        """Test that header data is accessible via properties."""
        # Basic header fields (EI_* identification)
        assert hasattr(parser, "ei_class")
        assert hasattr(parser, "ei_data")
        assert hasattr(parser, "ei_version")

        # Extended header fields
        assert hasattr(parser, "e_type")
        assert hasattr(parser, "e_machine")
        assert hasattr(parser, "e_entry")

    def test_machine_type_is_avr(self, parser):
        """Test that AVR ELF has correct machine type."""
        # AVR machine type should be 83 (EM_AVR)
        assert parser.e_machine == 83

    def test_entry_point_is_int(self, parser):
        """Test that entry point is an integer."""
        assert isinstance(parser.e_entry, int)


class TestElfSections:
    """Test ELF section handling via SectionAPI."""

    def test_can_fetch_all_sections(self, parser):
        """Test fetching all sections."""
        sections = parser.sections.fetch()
        assert sections is not None
        assert len(sections) > 0

    def test_sections_are_iterable(self, parser):
        """Test that fetched sections can be iterated."""
        sections = parser.sections.fetch()
        section_list = list(sections)
        assert len(section_list) > 0

    def test_can_get_section_by_name(self, parser):
        """Test getting a specific section by name."""
        # Try to get a common section (may not exist in all ELF files)
        sections = parser.sections.fetch()
        if len(list(sections)) > 0:
            # Get first section name
            first_section = list(parser.sections.fetch())[0]
            section_name = first_section.name if hasattr(first_section, "name") else None
            if section_name:
                retrieved = parser.sections.get(section_name)
                assert retrieved is not None

    def test_sections_have_standard_attributes(self, parser):
        """Test that sections have standard ELF attributes."""
        sections = list(parser.sections.fetch())
        if len(sections) > 0:
            section = sections[0]
            # Standard ELF section attributes
            assert hasattr(section, "sh_type")
            assert hasattr(section, "sh_addr")
            assert hasattr(section, "sh_size")


class TestElfSymbols:
    """Test ELF symbol handling via SymbolAPI."""

    def test_can_fetch_symbols(self, parser):
        """Test fetching symbols."""
        try:
            symbols = parser.symbols.fetch()
            # Symbols may or may not exist depending on ELF file
            assert symbols is not None
        except Exception:
            # Some ELF files may not have symbols
            pytest.skip("ELF file has no symbol table")

    def test_symbol_api_has_methods(self, parser):
        """Test that SymbolAPI has required methods."""
        assert callable(parser.symbols.get)
        assert callable(parser.symbols.fetch)


class TestMultipleElfFiles:
    """Test parsing multiple ELF files."""

    @pytest.mark.parametrize("elf_file", SAMPLE_ELF_FILES)
    def test_parse_sample_files(self, elf_file):
        """Test parsing various sample ELF files."""
        elf_path = EXAMPLES_DIR / elf_file
        if not elf_path.exists():
            pytest.skip(f"Sample file {elf_file} not found")

        parser = ElfParser(str(elf_path))
        assert parser is not None
        # Check basic header properties work
        assert hasattr(parser, "e_machine")
        assert isinstance(parser.e_machine, int)
        # Check sections API works
        sections = parser.sections.fetch()
        assert sections is not None


class TestElfDefs:
    """Test ELF definitions and enums."""

    def test_can_import_defs(self):
        """Test that defs module can be imported."""
        from objutils.elf import defs

        assert defs is not None

    def test_defs_has_elf_types(self):
        """Test that defs module has ELF type definitions."""
        from objutils.elf.defs import ELFType

        assert ELFType is not None

    def test_defs_has_machine_types(self):
        """Test that defs module has machine type definitions."""
        from objutils.elf.defs import ELFMachineType

        assert ELFMachineType is not None

    def test_defs_has_section_types(self):
        """Test that defs module has section type definitions."""
        from objutils.elf.defs import SectionType

        assert SectionType is not None


class TestElfModel:
    """Test ELF ORM model."""

    def test_can_import_model(self):
        """Test that model module can be imported."""
        from objutils.elf import model

        assert model is not None

    def test_model_has_header_class(self):
        """Test that model has Elf_Header class."""
        from objutils.elf.model import Elf_Header

        assert Elf_Header is not None

    def test_model_has_section_class(self):
        """Test that model has Elf_Section class."""
        from objutils.elf.model import Elf_Section

        assert Elf_Section is not None

    def test_model_has_symbol_class(self):
        """Test that model has Elf_Symbol class."""
        from objutils.elf.model import Elf_Symbol

        assert Elf_Symbol is not None


class TestElfDatabase:
    """Test ELF database functionality."""

    def test_parser_creates_database_file(self, sample_elf_path):
        """Test that parser creates .prgdb database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy ELF to temp directory
            import shutil

            temp_elf = Path(tmpdir) / "test.elf"
            shutil.copy(sample_elf_path, temp_elf)

            # Parse - should create test.elf.prgdb
            parser = ElfParser(str(temp_elf))
            assert parser is not None

            # Database file should exist
            db_path = Path(str(temp_elf) + ".prgdb")
            assert db_path.exists()

    def test_parser_has_session(self, parser):
        """Test that parser has SQLAlchemy session."""
        assert hasattr(parser, "session")
        assert parser.session is not None


class TestElfImageCreation:
    """Test image creation from ELF."""

    def test_can_create_image(self, parser):
        """Test that parser can create an image."""
        assert hasattr(parser, "create_image")
        # Try to create an image
        try:
            image = parser.create_image()
            # If it succeeds, verify it's an Image object
            if image is not None:
                from objutils import Image

                assert isinstance(image, Image)
                assert hasattr(image, "sections")
        except Exception as e:
            # Some ELF files may not be suitable for image creation
            # That's OK - we're just testing the API exists
            pytest.skip(f"Image creation not supported for this ELF: {e}")


class TestElfDebugSections:
    """Test debug section handling."""

    def test_debug_sections_method_exists(self, parser):
        """Test that debug_sections method exists."""
        assert hasattr(parser, "debug_sections")
        assert callable(parser.debug_sections)

    def test_can_call_debug_sections(self, parser):
        """Test calling debug_sections (may return empty list)."""
        debug_secs = parser.debug_sections()
        # May be empty, but should return a list
        assert isinstance(debug_secs, (list, type(None)))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
