"""DWARF DIE tree traversal with type resolution and variable value extraction.

This module provides the AttributeParser class, a comprehensive DWARF DIE traverser
that supports:
    - Type tree resolution with circular reference detection
    - Variable value extraction from ELF sections
    - Complex type handling (arrays, structs, pointers, typedefs)
    - DWARF expression evaluation for locations
    - Compile unit summaries

Key Components:
    **AttributeParser**: Main class for DIE tree traversal and type resolution
        - Resolves type references (handles CU-relative offsets)
        - Extracts variable values from memory images
        - Handles arrays (single/multi-dimensional), structs, scalars
        - Evaluates DWARF location expressions
        - Caches parsed types and DIE lookups (LRU)

    **Variable**: Dataclass representing a variable with location and type info
    **DIE**: Lightweight representation of a Debug Information Entry
    **CompiledUnit**: Summary info for compilation units
    **CircularReference**: Marker for self-referential types

Architecture:
    The AttributeParser combines:
    1. **ELF ORM Layer** (SQLAlchemy) - Query DIEs from database
    2. **DWARF Readers** - Decode DWARF-encoded data
    3. **Stack Machine** - Evaluate DWARF expressions
    4. **Image Access** - Read values from ELF section images

Type Resolution:
    Types are represented as DIE trees with:
    - **tag**: DWARF tag (base_type, pointer_type, structure_type, etc.)
    - **attributes**: Dict of attribute name -> value
    - **children**: List of child DIEs (struct members, array bounds, etc.)

    Type references (DW_AT_type) are recursively resolved, with special handling for:
    - CU-relative reference forms (DW_FORM_ref1/2/4/8/udata)
    - Typedef chains and type qualifiers (const, volatile, restrict)
    - Circular references (linked lists, recursive structs)

Variable Value Extraction:
    The get_value() method extracts variable values from ELF section images:
    - **Scalars**: Read directly via typed image access (uint32_le, float64_be, etc.)
    - **Arrays**: Bulk read with automatic reshaping for multi-dimensional arrays
    - **Structs**: Recursively extract members at calculated offsets
    - **Pointers**: Treated as unsigned integers (address values)

Location Resolution:
    Variable locations are resolved via:
    1. **ELF Symbol Table** (elf_location) - Preferred, most reliable
    2. **DWARF Expressions** (dwarf_location) - Evaluated by stack machine
    3. **Static Analysis** - Calculated offsets for struct members

Usage Example:
    ```python
    from objutils.elf import ElfParser
    from objutils.dwarf import DwarfProcessor
    from objutils.dwarf.traverser import AttributeParser

    # Parse ELF and import DWARF info
    ep = ElfParser("firmware.elf")
    dp = DwarfProcessor(ep)
    dp.do_dbg_info()

    # Create parser (opens existing .prgdb or imports from ELF)
    parser = AttributeParser("firmware.elf")

    # Get variable and extract value
    die = parser.session.query(DebugInformationEntry).filter_by(tag="variable").first()
    var = parser.variable(die)
    value = parser.get_value(var)
    print(f"{var.name} = {value}")

    # Traverse DIE tree with formatted output
    root = parser.session.query(DebugInformationEntry).first()
    parser.traverse_tree(root)

    # Parse type tree
    type_tree = parser.type_tree(die)  # Accepts DIE, offset, or DW_AT_type attribute
    ```

Compile Unit Summaries:
    ```python
    from objutils.dwarf.traverser import CompiledUnitsSummary

    summary = CompiledUnitsSummary(session)
    # Prints organized list of compilation units by directory
    ```

Performance Optimizations:
    - LRU cache (64K entries) on type_tree() method
    - LRU cache (8K entries) on get_die() and parse_attributes()
    - Leverages attributes_map for O(1) attribute access
    - Bulk array reads via read_numeric_array()
    - Shared type cache prevents redundant parsing

Type Encoding Constants:
    DWARF_TYPE_ENCODINGS: frozenset of tags representing type DIEs
    DATA_REPRESENTATION: Mapping of attributes to their enum types

ORM Schema Requirements:
    - model.DebugInformationEntry with offset, tag, abbrev, attributes, children
    - model.DIEAttribute with name, raw_value, form
    - model.Elf_Section with section_name, section_image, sh_addr
    - model.Elf_Symbol with symbol_name, st_value, section_name
    - model.Elf_Header with address_size, endianess, is_64bit

See Also:
    - objutils.dwarf.attrparser: Simpler DIE traverser without value extraction
    - objutils.dwarf.c_generator: Generates C code from DIE trees
    - objutils.dwarf.readers: DWARF binary readers
    - objutils.dwarf.sm: DWARF expression stack machine
"""

from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import groupby
from typing import Any, Optional, Union

from objutils import Image, Section
from objutils.dwarf.constants import (
    Accessibility,
    AttributeEncoding,
    AttributeForm,
    BaseTypeEncoding,
    CallingConvention,
    DecimalSign,
    Defaulted,
    DiscriminantDescriptor,
    Endianity,
    IdentifierCase,
    Inline,
    Languages,
    Ordering,
    Tag,
    Virtuality,
    Visibility,
)
from objutils.dwarf.encoding import Endianess
from objutils.dwarf.readers import DwarfReaders
from objutils.elf import defs, model
from objutils.elf.model import DIEAttribute


DWARF_TYPE_ENCODINGS = frozenset(
    {
        Tag.base_type,
        Tag.pointer_type,
        Tag.reference_type,
        Tag.rvalue_reference_type,
        Tag.const_type,
        Tag.volatile_type,
        Tag.restrict_type,
        Tag.typedef,
        Tag.structure_type,
        Tag.class_type,
        Tag.union_type,
        Tag.array_type,
        Tag.enumeration_type,
        Tag.subroutine_type,
        Tag.unspecified_type,
        Tag.interface_type,
        Tag.ptr_to_member_type,
        Tag.set_type,
        Tag.shared_type,
    }
)
"""frozenset: DWARF tags that represent type definitions.

Used to identify DIEs that define types (as opposed to variables, functions, etc.).
Includes base types, derived types (pointers, arrays), composite types (structs,
unions, classes), and special types (typedefs, subroutines, enumerations).
"""


def is_type_encoding(encoding: Union[int, AttributeEncoding]) -> bool:
    """Check if a DWARF tag represents a type definition.

    Args:
        encoding: DWARF tag value (int or AttributeEncoding enum)

    Returns:
        True if the tag represents a type, False otherwise

    Example:
        ```python
        is_type_encoding(Tag.base_type)         # True
        is_type_encoding(Tag.variable)          # False
        is_type_encoding(Tag.structure_type)    # True
        ```
    """
    return encoding in DWARF_TYPE_ENCODINGS


@dataclass
class CompiledUnit:
    """Summary information for a DWARF compilation unit.

    Attributes:
        name: Source file name (e.g., "main.c")
        comp_dir: Compilation directory path
        producer: Compiler identification string (e.g., "GCC 11.2.0")
        language: Programming language (e.g., "DW_LANG_C99")
    """

    name: str
    comp_dir: str
    producer: str
    language: str


@dataclass
class DIE:
    """Lightweight representation of a DWARF Debugging Information Entry.

    Used as an alternative to the full ORM model for parsed type trees.
    More efficient for caching and serialization than full model objects.

    Attributes:
        tag: DWARF tag name (e.g., "base_type", "structure_type", "variable")
        children: List of child DIEs (e.g., struct members, array bounds)
        attributes: Dict mapping attribute names to decoded values
    """

    tag: str
    children: list[Any] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Variable:
    """Represents a DWARF variable with location and type information.

    Attributes:
        name: Variable name from DW_AT_name
        section: ELF section name containing the variable (e.g., ".data", ".bss")
        elf_location: Address from ELF symbol table (most reliable)
        dwarf_location: Decoded DWARF location expression (fallback)
        static: True if variable has internal linkage (static storage)
        type_desc: Parsed type tree (DIE or dict) describing the variable's type
        _allocated: True if variable is in an allocated section (has image data)

    Note:
        Variables in .bss or other non-allocated sections have _allocated=False
        and cannot have their values extracted.
    """

    name: str
    section: Optional[str] = field(default=None)
    elf_location: Optional[int] = field(default=None)
    dwarf_location: Optional[str] = field(default=None)
    static: bool = field(default=False)
    type_desc: Optional[DIE] = field(default=None)
    _allocated: bool = field(default=False, repr=False)


DATA_REPRESENTATION = {
    "encoding": BaseTypeEncoding,
    "decimal_sign": DecimalSign,
    "endianity": Endianity,
    "accessibility": Accessibility,
    "visibility": Visibility,
    "virtuality": Virtuality,
    "language": Languages,
    "identifier_case": IdentifierCase,
    "calling_convention": CallingConvention,
    "inline": Inline,
    "ordering": Ordering,
    "discr_list": DiscriminantDescriptor,
    "defaulted": Defaulted,
    "byte_size": int,
    "upper_bound": int,
    "lower_bound": int,
    "containing_type": int,
    "object_pointer": int,
}
"""dict: Mapping of DWARF attribute names to their Python type converters.

Used during attribute parsing to convert raw integer values into more meaningful
representations (enums or typed values). For example, the "encoding" attribute
is converted from an integer to a BaseTypeEncoding enum value.

Keys are attribute names (str), values are type converters (enum classes or int).
"""


# 'data_member_location': b'#\x00',


def get_attribute(attrs: dict[str, DIEAttribute], key: str, default: Union[int, str]) -> Union[int, str]:
    """Get attribute value from attributes_map with fallback default.

    Args:
        attrs: Attribute map (dict of name -> DIEAttribute)
        key: Attribute name to retrieve
        default: Default value if attribute not found

    Returns:
        Attribute's raw_value if found, otherwise the default value

    Example:
        ```python
        name = get_attribute(die.attributes_map, "name", "unnamed")
        size = get_attribute(die.attributes_map, "byte_size", 0)
        ```
    """
    attr: Optional[DIEAttribute] = attrs.get(key)
    if attr is None:
        return default
    else:
        return attr.raw_value


class CompiledUnitsSummary:
    """Generate organized summary of compilation units grouped by directory.

    Queries all compilation units from the database, groups them by compilation
    directory, and prints a formatted report showing source files, compilers,
    and languages used.

    Args:
        session: SQLAlchemy session connected to DWARF database

    Example:
        ```python
        summary = CompiledUnitsSummary(session)
        # Output:
        # Compile Units in Directory: /home/user/project/src
        #
        #     main.c, Producer: 'GCC 11.2.0', Language: 'DW_LANG_C99'
        #     utils.c, Producer: 'GCC 11.2.0', Language: 'DW_LANG_C99'
        #
        # Types used in Compile Units: constant, subprogram, variable, ...
        ```

    Note:
        Constructor immediately prints the summary to stdout.
    """

    def __init__(self, session) -> None:
        """Create and print compilation unit summary.

        Args:
            session: SQLAlchemy session with DebugInformationEntry populated
        """
        cus = session.query(model.DebugInformationEntry).filter(model.DebugInformationEntry.tag == Tag.compile_unit).all()
        units = []
        tps = set()
        for cu in cus:
            name = get_attribute(cu.attributes_map, "name", "N/A")
            producer = get_attribute(cu.attributes_map, "producer", "N/A")
            comp_dir = get_attribute(cu.attributes_map, "comp_dir", "N/A")
            language = get_attribute(cu.attributes_map, "language", "N/A")
            units.append(CompiledUnit(name=name, comp_dir=comp_dir, producer=producer, language=language))
            for ch in cu.children:
                tps.add(ch.abbrev.tag)
                if ch.abbrev.tag == "variable":
                    if "type" not in ch.attributes_map:
                        print(f"\t\tVariable without type: {ch.attributes_map}")
                    else:
                        tpx = int(ch.attributes_map["type"].raw_value)
                        tp = session.query(model.DebugInformationEntry).filter(model.DebugInformationEntry.offset == tpx).first()
                        print(tp.attributes_map)

        groups = groupby(sorted(units, key=lambda x: x.comp_dir), key=lambda x: x.comp_dir)
        for group in groups:
            print(f"\nCompile Units in Directory: {group[0]}", end="\n\n")
            for cu in sorted(group[1], key=lambda x: x.name):
                print(f"    {cu.name}, Producer: {cu.producer!r}, Language: {cu.language!r}")
        print(f"\nTypes used in Compile Units: {', '.join(sorted(tps))}")


def compile_units_summary(session) -> None:
    """Print simple list of all compilation units with metadata.

    Alternative to CompiledUnitsSummary that prints a flat list without grouping.

    Args:
        session: SQLAlchemy session connected to DWARF database

    Example:
        ```python
        compile_units_summary(session)
        # Output:
        # Compile Unit #0: 'main.c', Name: '/home/user/project' Producer: 'GCC 11.2.0', ...
        # Compile Unit #1: 'utils.c', Name: '/home/user/project' Producer: 'GCC 11.2.0', ...
        ```
    """
    cus = session.query(model.DebugInformationEntry).filter(model.DebugInformationEntry.tag == Tag.compile_unit).all()
    for idx, cu in enumerate(cus):
        name = cu.attributes_map.get("name", "N/A").raw_value
        producer = cu.attributes_map.get("producer", "N/A").raw_value
        comp_dir = cu.attributes_map.get("comp_dir", "N/A").raw_value
        language = cu.attributes_map.get("language", "N/A").raw_value
        print(f"Compile Unit #{idx}: {name!r}, Name: {comp_dir!r} Producer: {producer!r}, Language: {language!r}")


@dataclass
class CircularReference:
    """Marker for circular type references in DWARF type graphs.

    When parse_type() detects a cycle (a type that references itself directly
    or indirectly), it returns this sentinel object instead of recursing infinitely.

    Attributes:
        tag: The DWARF tag of the circular type (e.g., "structure_type")
        name: The name of the type if available, empty string otherwise

    Example:
        ```python
        # Linked list node with pointer to itself:
        # struct node { struct node *next; };

        type_dict = parser.parse_type(offset)
        if isinstance(type_dict, CircularReference):
            print(f"Circular: {type_dict.tag} '{type_dict.name}'")
        ```

    Note:
        This is a duplicate of the CircularReference class in attrparser.py.
        Both exist for module independence.
    """

    tag: str
    name: str


class AttributeParser:
    """Comprehensive DWARF DIE traverser with type resolution and value extraction.

    This parser provides advanced DWARF debugging information analysis with:
        - Type tree resolution following DW_AT_type references
        - Variable value extraction from ELF section images
        - Complex type handling (arrays, structs, pointers, typedefs, qualifiers)
        - DWARF location expression evaluation
        - Circular reference detection for recursive types
        - Multi-level caching for performance

    The AttributeParser can be initialized with either:
        1. An existing SQLAlchemy session (backward compatible)
        2. A filesystem path to an ELF file or .prgdb database

    When given a path, the parser automatically:
        - Opens or creates a .prgdb database file
        - Imports DWARF info from ELF if needed
        - Connects to the database session

    Caching Strategy:
        - **type_tree()**: LRU cache (64K entries) for complete type trees
        - **get_die()**: LRU cache (8K entries) for DIE lookups by offset
        - **parse_attributes()**: LRU cache (8K entries) for attribute parsing
        - **parsed_types**: Per-instance dict cache for type dictionaries
        - **type_stack**: Runtime cycle detection set

    Type Resolution:
        Types are parsed into DIE objects with:
        - **tag**: DWARF tag name (e.g., "base_type", "pointer_type")
        - **attributes**: Dict of attribute name -> converted value
        - **children**: List of child DIEs (struct members, array bounds, etc.)

        CU-relative reference forms (DW_FORM_ref1/2/4/8/udata) are automatically
        converted to absolute offsets using the DIE's cu_start attribute.

    Value Extraction:
        The get_value() method handles:
        - **Scalars**: Direct typed reads (uint32_le, float64_be, etc.)
        - **Arrays**: Bulk reads with automatic multi-dimensional reshaping
        - **Structs**: Recursive member extraction at calculated offsets
        - **Pointers**: Treated as unsigned integers (address values)
        - **Typedefs/Qualifiers**: Automatically unwrapped to base types

    Location Resolution Priority:
        1. ELF Symbol Table (elf_location) - Most reliable
        2. DWARF Expression (dwarf_location) - Evaluated by stack machine
        3. Calculated Offsets (for struct members)

    Attributes:
        session: SQLAlchemy session for ORM queries
        type_stack: Set tracking offsets being parsed (cycle detection)
        parsed_types: Cache mapping offset -> parsed DIE
        att_types: Statistics dict mapping tag -> set of attribute names seen
        allocated_sections: Frozenset of section names with allocated images
        image: Image object for reading section data
        endianess: Little or Big endian (from ELF header)
        is_64bit: True for 64-bit ELF files
        readers: Dict of DWARF attribute readers by form
        section_readers: Dict mapping (encoding, size) -> typed reader name
        stack_machine: DWARF expression evaluator
        dwarf_expression: Helper for decoding location expressions

    Class Attributes:
        STOP_LIST: Attributes excluded from parsed type dictionaries
            (sibling, decl_file, decl_line, decl_column, declaration,
             specification, abstract_origin)

    Example:
        ```python
        # Initialize from ELF file path (imports DWARF if needed)
        parser = AttributeParser("firmware.elf")

        # Get variable and extract value
        die = parser.session.query(DebugInformationEntry).filter_by(tag="variable").first()
        var = parser.variable(die)
        value = parser.get_value(var)
        print(f"{var.name} = {value}")

        # Parse type tree
        type_tree = parser.type_tree(die)  # Accepts DIE, offset, or attribute

        # Traverse DIE tree with formatted output
        root = parser.session.query(DebugInformationEntry).first()
        parser.traverse_tree(root)
        ```

    Note:
        Variables in non-allocated sections (.bss, .debug_*, etc.) cannot
        have their values extracted and will return None from get_value().
    """

    # Attributes considered non-structural for high-level type dicts
    STOP_LIST: set[str] = {
        "sibling",
        "decl_file",
        "decl_line",
        "decl_column",
        "declaration",
        "specification",
        "abstract_origin",
    }

    def __init__(self, session_or_path, *, import_if_needed: bool = True, force_import: bool = False, quiet: bool = True):
        """Initialize AttributeParser with session or ELF/database path.

        Args:
            session_or_path: Either:
                - SQLAlchemy session (backward compatible)
                - Path to ELF file (str or Path) - opens/creates .prgdb
                - Path to .prgdb file (str or Path) - opens existing database
            import_if_needed: When True, import DWARF from ELF if .prgdb doesn't exist
            force_import: When True, re-import DWARF even if .prgdb exists
            quiet: When True, suppress non-error output during import

        Raises:
            FileNotFoundError: If path doesn't exist
            ValueError: If database is corrupt or incompatible

        Example:
            ```python
            # From existing session
            parser = AttributeParser(session)

            # From ELF (auto-imports to firmware.prgdb)
            parser = AttributeParser("firmware.elf")

            # From existing database
            parser = AttributeParser("firmware.prgdb")

            # Force re-import
            parser = AttributeParser("firmware.elf", force_import=True)
            ```
        """
        # Lazy import to avoid heavy module import/cycles at module import time.
        from objutils.elf import open_program_database  # local import by design

        # Determine whether we received a session or a filesystem path.
        if hasattr(session_or_path, "query"):
            # Assume it's a SQLAlchemy session (backward compatible path)
            self.session = session_or_path
            self._model = None
        else:
            # Treat as a path (str or Path-like)
            db_model = open_program_database(
                session_or_path,
                import_if_needed=import_if_needed,
                force_import=force_import,
                quiet=quiet,
            )
            self._model = db_model
            self.session = db_model.session
        self.type_stack: set[int] = set()
        self.parsed_types: dict = {}
        self.att_types: dict = defaultdict(set)
        self.allocated_sections: frozenset[str] = frozenset(
            s[0]
            for s in self.session.query(model.Elf_Section.section_name)
            .filter(model.Elf_Section.progbits, model.Elf_Section.flag_alloc)
            .all()
        )
        sections = []
        for item in (
            self.session.query(model.Elf_Section.sh_addr, model.Elf_Section.section_image)
            .filter(model.Elf_Section.progbits, model.Elf_Section.flag_alloc)
            .all()
        ):
            if item[1] is not None:  # Check for section data.
                sections.append(Section(*item))
        self.image = Image(sections)
        debug_str_section = self.session.query(model.Elf_Section).filter_by(section_name=".debug_str").first()
        if debug_str_section:
            debug_str = debug_str_section.section_image
        else:
            debug_str = b""
        debug_line_str_section = self.session.query(model.Elf_Section).filter_by(section_name=".debug_line_str").first()
        if debug_line_str_section:
            debug_line_str = debug_line_str_section.section_image
        else:
            debug_line_str = b""
        elf_header = self.session.query(model.Elf_Header).first()
        if elf_header is None:
            address_size = 4
            endianess = Endianess.Little
            is_64bit = False
        else:
            address_size = elf_header.address_size
            endianess = Endianess.Little if elf_header.endianess == defs.ELFDataEncoding.ELFDATA2LSB else Endianess.Big
            is_64bit = elf_header.is_64bit
        factory = DwarfReaders(
            endianess=endianess,
            address_size=address_size,
            strings=debug_str,
            line_strings=debug_line_str,
        )
        # BaseTypeEncoding
        self.endianess = endianess
        self.is_64bit = is_64bit
        self.readers = factory.readers
        postfix = "_le" if (endianess == Endianess.Little) else "_be"
        self.stack_machine = factory.stack_machine
        self.section_readers = {
            (BaseTypeEncoding.unsigned_char, 1): f"uint8{postfix}",
            (BaseTypeEncoding.signed_char, 1): f"int8{postfix}",
            (BaseTypeEncoding.unsigned, 2): f"uint16{postfix}",
            (BaseTypeEncoding.unsigned, 4): f"uint32{postfix}",
            (BaseTypeEncoding.unsigned, 8): f"uint64{postfix}",
            (BaseTypeEncoding.signed, 2): f"int16{postfix}",
            (BaseTypeEncoding.signed, 4): f"int32{postfix}",
            (BaseTypeEncoding.signed, 8): f"int64{postfix}",
            (BaseTypeEncoding.float, 4): f"float32{postfix}",
            (BaseTypeEncoding.float, 8): f"float64{postfix}",
        }
        self.dwarf_expression = factory.dwarf_expression

    @lru_cache(maxsize=64 * 1024)
    def type_tree(self, obj: Union[int, model.DebugInformationEntry, DIEAttribute]) -> dict[str, Any] | CircularReference:
        """Resolve and return complete type tree for a DIE, offset, or attribute.

        This method accepts multiple input types for convenience:
            - **int**: Absolute DIE offset
            - **DebugInformationEntry**: DIE with DW_AT_type attribute
            - **DIEAttribute**: DW_AT_type attribute referencing a type

        The returned type tree is a nested DIE structure with:
            - **tag**: DWARF tag name for the type DIE
            - **attributes**: Dict of attribute name -> value (type refs recursively resolved)
            - **children**: List of child DIE objects (members, enumerators, etc.)

        Args:
            obj: One of:
                - Absolute DIE offset (int)
                - DIE instance that has a DW_AT_type attribute
                - DIEAttribute instance (DW_AT_type) referencing a type

        Returns:
            DIE object representing the complete type tree, or CircularReference
            if a cycle is detected. Returns dict with "<invalid>" or "<no-type>"
            tag on errors.

        Example:
            ```python
            # From offset
            type_tree = parser.type_tree(0x1234)

            # From DIE
            var_die = session.query(DebugInformationEntry).filter_by(tag="variable").first()
            type_tree = parser.type_tree(var_die)

            # From attribute
            type_attr = var_die.attributes_map["type"]
            type_tree = parser.type_tree(type_attr)
            ```

        Note:
            Results are cached with LRU cache (64K entries). CU-relative reference
            forms are automatically converted to absolute offsets.
        """
        result = None
        # Case 1: already an absolute DIE offset
        if isinstance(obj, int):
            return self.parse_type(obj)

        # Case 2: attribute object (expected to be DW_AT_type)
        if isinstance(obj, DIEAttribute):
            # Try to resolve relative ref forms to absolute offset using the parent DIE if available
            parent: Optional[model.DebugInformationEntry] = getattr(obj, "entry", None)
            off = self._resolve_type_offset(obj, parent)
            if off is None:
                return {"tag": "<invalid>", "attrs": {}}
            return self.parse_type(off)

        # Case 3: a DIE that should have a DW_AT_type attribute
        if hasattr(obj, "attributes_map") or hasattr(obj, "attributes"):
            die = obj  # type: ignore[assignment]
            type_attr = self._get_attr(die, "type")
            if type_attr is None:
                return {"tag": "<no-type>", "attrs": {}}
            off = self._resolve_type_offset(type_attr, die)
            if off is None:
                return {"tag": "<invalid>", "attrs": {}}
            result = self.parse_type(off)
        return result

        # Fallback
        return {"tag": "<unsupported>", "attrs": {}}

    def variable(self, obj: model.DebugInformationEntry) -> Variable:
        """Create Variable object from variable DIE with resolved type and location.

        Args:
            obj: DIE with tag="variable"

        Returns:
            Variable object with name, type, location info, and allocation status

        Example:
            ```python
            var_die = session.query(DebugInformationEntry).filter_by(tag="variable").first()
            var = parser.variable(var_die)
            print(f"{var.name}: type={var.type_desc.tag}, addr=0x{var.elf_location:x}")
            ```
        """
        name = self._attr_raw(obj, "name")
        type_desc = self.type_tree(obj)
        external = self._attr_raw(obj, "external")
        if external is not None:
            static = int(external) == 0
        else:
            static = False
        sym = (
            self.session.query(model.Elf_Symbol.section_name, model.Elf_Symbol.st_value)
            .filter(model.Elf_Symbol.symbol_name == name)
            .first()
        )
        if sym:
            section_name, elf_location = sym
        else:
            section_name = None
            elf_location = None
        location = self._get_attr(obj, "location")
        if location is not None:
            dwarf_location = self.dwarf_expression(location.form, location.raw_value)
        else:
            dwarf_location = None
        return Variable(
            name=name,
            static=static,
            type_desc=type_desc,
            section=section_name,
            elf_location=elf_location,
            dwarf_location=dwarf_location,
            _allocated=section_name in self.allocated_sections,
        )

    def get_value(self, var: Variable) -> Optional[Any]:
        """Extract variable value from ELF section image.

        This method resolves the variable's address and extracts its value based
        on its DWARF type description. Handles scalars, arrays, structs, pointers,
        and nested combinations.

        Supported Types:
            - **Scalars**: int8-64, uint8-64, float32/64 (all endiannesses)
            - **Arrays**: Single and multi-dimensional, any element type
            - **Structs**: Recursive extraction of all members
            - **Pointers**: Returned as unsigned integer (address value)
            - **Typedefs/Qualifiers**: Automatically unwrapped

        Address Resolution (in order of preference):
            1. var.elf_location (from ELF symbol table)
            2. var.dwarf_location (decoded DWARF expression)
            3. None (for struct members - calculated from parent)

        Args:
            var: Variable object with type_desc and location info

        Returns:
            Extracted value:
                - **Scalar**: int or float
                - **Array**: Nested lists matching array dimensions
                - **Struct**: Dict mapping member names to values
                - **None**: If variable not in allocated section or address unresolvable

        Example:
            ```python
            var = parser.variable(var_die)
            value = parser.get_value(var)

            # Scalar: value = 42
            # Array: value = [[1, 2], [3, 4]]
            # Struct: value = {"x": 10, "y": 20.5}
            ```

        Note:
            Variables in .bss or other non-allocated sections return None.
            Type qualifiers (const, volatile, restrict) are transparent.
        """
        if not var._allocated:
            # No image for variable, i.e. .bss section and the like.
            return None
        # 1) Resolve address
        addr: Optional[int] = None
        if isinstance(var.elf_location, int):
            addr = var.elf_location
        elif var.dwarf_location is not None:
            loc = var.dwarf_location
            try:
                if isinstance(loc, int):
                    addr = int(loc)
                elif isinstance(loc, str):
                    s = loc.strip()
                    if s.startswith("addr(") and s.endswith(")"):
                        inner = s[s.find("(") + 1 : -1]
                        addr = int(inner, 0)
                    elif s.startswith("0x"):
                        addr = int(s, 16)
            except Exception:
                addr = None

        if addr is None:
            return None

        # 2a) Helpers to work with both dict-based and DIE-based nodes
        def _get_tag(node: Any) -> Optional[str]:
            if node is None:
                return None
            if isinstance(node, dict):
                return node.get("tag")
            if isinstance(node, DIE):
                return node.tag
            if isinstance(node, CircularReference):
                return None
            return None

        def _get_attrs(node: Any) -> dict:
            if node is None:
                return {}
            if isinstance(node, dict):
                return node.get("attributes") or node.get("attrs") or {}
            if isinstance(node, DIE):
                return node.attributes or {}
            return {}

        def _get_children(node: Any) -> list[Any]:
            if node is None:
                return []
            if isinstance(node, dict):
                return node.get("children") or []
            if isinstance(node, DIE):
                return node.children or []
            return []

        def _get_nested_type(node: Any) -> Any:
            attrs = _get_attrs(node)
            return attrs.get("type")

        # 2b) Unwrap qualifiers (typedef, const, etc.)
        def _unwrap_qualifiers(node: Any) -> Any:
            seen = 0
            cur = node
            while cur is not None and seen < 64:
                seen += 1
                tag = _get_tag(cur)
                if tag in {"typedef", "const_type", "volatile_type", "restrict_type"}:
                    cur = _get_nested_type(cur)
                    continue
                break
            return cur

        # 2c) Try to detect arrays first (do not unwrap past array_type)
        def _unwrap_qualifiers_until_array(node: Any) -> Any:
            seen = 0
            cur = node
            while cur is not None and seen < 64:
                seen += 1
                tag = _get_tag(cur)
                if tag == "array_type":
                    return cur
                if tag in {"typedef", "const_type", "volatile_type", "restrict_type"}:
                    cur = _get_nested_type(cur)
                    continue
                break
            return cur

        # 2d) Unwrap qualifiers all the way down to base_type
        def unwrap_to_base(d: Optional[DIE | dict | CircularReference]) -> Optional[DIE]:
            # Accept DIE or dict-like from older structures
            seen = 0
            current = d
            while current is not None and seen < 32:
                seen += 1
                if isinstance(current, CircularReference):
                    return None
                tag = _get_tag(current)
                attrs = _get_attrs(current)
                if tag == "base_type":
                    # Normalize into DIE for downstream code
                    if isinstance(current, DIE):
                        return current
                    die = DIE("base_type")
                    die.attributes.update(attrs)
                    return die
                # unwrap 'type' attribute if present
                current = attrs.get("type")
                continue
                # Unknown node
                break
            return None

        # 2e) If the type is an array, support nested arrays and arrays of composites
        node0 = _unwrap_qualifiers_until_array(var.type_desc)
        if _get_tag(node0) == "array_type":
            # Gather dimensions across nested array_type nodes and return leaf element type
            def _dims_and_leaf(node: Any) -> tuple[list[int], Any]:
                dims: list[int] = []
                cur = node
                hop = 0
                while cur is not None and hop < 64 and _get_tag(cur) == "array_type":
                    hop += 1
                    # compute dimension(s) on this level
                    sr_children = [c for c in _get_children(cur) if _get_tag(c) == "subrange_type"]
                    dim_this_level = 1
                    found_any = False
                    for sr in sr_children:
                        if _get_tag(sr) != "subrange_type":
                            continue
                        sr_attrs = _get_attrs(sr)
                        lb_attr = sr_attrs.get("lower_bound")
                        try:
                            lb = int(lb_attr) if lb_attr is not None else 0
                        except Exception:
                            lb = 0
                        ub_attr = sr_attrs.get("upper_bound")
                        if ub_attr is None:
                            cnt = sr_attrs.get("count")
                            if cnt is None:
                                continue
                            try:
                                dim = int(cnt)
                            except Exception:
                                continue
                        else:
                            try:
                                ub = int(ub_attr)
                                dim = ub - lb + 1
                            except Exception:
                                continue
                        if dim <= 0:
                            continue
                        dim_this_level *= dim
                        found_any = True
                    if not found_any:
                        # No subrange info -> cannot proceed
                        return [], None
                    dims.append(dim_this_level)
                    # advance to nested element type, unwrapping qualifiers between arrays
                    cur = _get_nested_type(cur)
                    while _get_tag(cur) in {"typedef", "const_type", "volatile_type", "restrict_type"}:
                        cur = _get_nested_type(cur)
                return dims, cur

            def _reshape(flat: list[Any], dims: list[int]) -> list[Any]:
                # Recursively reshape flat list into nested list according to dims
                if not dims:
                    return flat
                if len(dims) == 1:
                    return list(flat[: dims[0]])
                size_per = 1
                for d in dims[1:]:
                    size_per *= d
                out: list[Any] = []
                for i in range(dims[0]):
                    chunk = flat[i * size_per : (i + 1) * size_per]
                    out.append(_reshape(chunk, dims[1:]))
                return out

            def _element_size(elem: Any) -> Optional[int]:
                t = _get_tag(elem)
                attrs = _get_attrs(elem)
                if t in {"base_type", "pointer_type"}:
                    try:
                        return int(attrs.get("byte_size"))
                    except Exception:
                        return None
                bsz = attrs.get("byte_size")
                try:
                    return int(bsz) if bsz is not None else None
                except Exception:
                    return None

            dims, leaf = _dims_and_leaf(node0)
            if not dims or leaf is None:
                return None

            # Try bulk read for numeric or pointer leaves
            leaf_tag = _get_tag(leaf)
            postfix = "_le" if (self.endianess == Endianess.Little) else "_be"
            if leaf_tag == "base_type":
                base = unwrap_to_base(leaf)
                if base is not None:
                    encoding = base.attributes.get("encoding")
                    byte_size = base.attributes.get("byte_size")
                    try:
                        key = (encoding, int(byte_size))
                    except Exception:
                        key = None
                    dtype = self.section_readers.get(key) if key is not None else None
                    if dtype:
                        total_len = 1
                        for d in dims:
                            total_len *= d
                        try:
                            flat_vals = list(self.image.read_numeric_array(addr, int(total_len), dtype))
                            return _reshape(flat_vals, dims)
                        except Exception:
                            return None
            elif leaf_tag == "pointer_type":
                attrs = _get_attrs(leaf)
                bsz = attrs.get("byte_size")
                try:
                    bits = int(bsz) * 8
                    dtype = f"uint{bits}{postfix}"
                except Exception:
                    dtype = None
                if dtype:
                    total_len = 1
                    for d in dims:
                        total_len *= d
                    try:
                        flat_vals = list(self.image.read_numeric_array(addr, int(total_len), dtype))
                        return _reshape(flat_vals, dims)
                    except Exception:
                        return None

            # Fallback for composite element (e.g., struct/union or other non-numeric): iterate elements
            esz = _element_size(leaf)
            if esz is None or esz <= 0:
                return None
            total_len = 1
            for d in dims:
                total_len *= d
            flat_results: list[Any] = []
            for i in range(total_len):
                elem_addr = addr + i * esz
                elem_var = Variable(
                    name=f"elem_{i}",
                    static=False,
                    type_desc=leaf,
                    section=var.section,
                    elf_location=elem_addr,
                    dwarf_location=None,
                    _allocated=var._allocated,
                )
                flat_results.append(self.get_value(elem_var))
            return _reshape(flat_results, dims)

        # 2f) Handle structure types
        node1 = _unwrap_qualifiers(var.type_desc)
        if _get_tag(node1) == "structure_type":
            struct_dict = {}
            for member in _get_children(node1):
                if _get_tag(member) != "member":
                    continue
                member_attrs = _get_attrs(member)
                member_name = member_attrs.get("name")
                if not member_name:
                    continue

                member_loc_attr = member_attrs.get("data_member_location")
                member_offset = 0
                if isinstance(member_loc_attr, (str, bytes)):
                    # Handle simple 'plus_uconst(offset)'
                    loc_str = member_loc_attr.decode() if isinstance(member_loc_attr, bytes) else member_loc_attr
                    if loc_str.startswith("plus_uconst(") and loc_str.endswith(")"):
                        try:
                            member_offset = int(loc_str[len("plus_uconst(") : -1], 0)
                        except ValueError:
                            pass  # Fallback to offset 0
                elif isinstance(member_loc_attr, int):
                    member_offset = member_loc_attr

                member_addr = addr + member_offset
                member_type = _get_nested_type(member)

                # Create a temporary Variable-like object for the member to recursively get its value.
                member_var = Variable(
                    name=member_name,
                    static=False,  # Not strictly correct, but sufficient for get_value
                    type_desc=member_type,
                    section=var.section,
                    elf_location=member_addr,
                    dwarf_location=None,
                    _allocated=var._allocated,
                )
                struct_dict[member_name] = self.get_value(member_var)
            return struct_dict

        # 2g) Walk type description to base_type for scalars
        base = unwrap_to_base(var.type_desc)
        if base is None:
            return None

        # 3) Determine reader dtype from encoding and size
        encoding = base.attributes.get("encoding")
        byte_size = base.attributes.get("byte_size")
        if encoding is None or byte_size is None:
            return None
        try:
            key = (encoding, int(byte_size))
        except Exception:
            return None
        dtype = self.section_readers.get(key)
        if not dtype:
            return None

        # 4) Read and return the value
        try:
            return self.image.read_numeric(addr, dtype)
        except Exception:
            return None

    def _resolve_type_offset(
        self,
        type_attr: DIEAttribute,
        context_die: Optional[model.DebugInformationEntry],
    ) -> Optional[int]:
        """Resolve DW_AT_type attribute value to absolute DIE offset.

        Handles CU-relative reference forms (DW_FORM_ref1/2/4/8/udata) by adding
        the context DIE's cu_start attribute to convert to absolute offset.

        Args:
            type_attr: DW_AT_type attribute with raw_value and form
            context_die: Parent DIE providing cu_start for CU-relative refs

        Returns:
            Absolute DIE offset, or None if attribute cannot be interpreted

        Note:
            CU-relative forms are automatically detected and adjusted.
            Other forms (DW_FORM_ref_addr, etc.) are assumed absolute.
        """
        raw = getattr(type_attr, "raw_value", None)
        try:
            off = int(raw) if raw is not None else None
        except Exception:
            off = None
        if off is None:
            return None
        try:
            frm = getattr(type_attr, "form", None)
            if frm in (
                getattr(AttributeForm, "DW_FORM_ref1", None),
                getattr(AttributeForm, "DW_FORM_ref2", None),
                getattr(AttributeForm, "DW_FORM_ref4", None),
                getattr(AttributeForm, "DW_FORM_ref8", None),
                getattr(AttributeForm, "DW_FORM_ref_udata", None),
            ):
                base = getattr(context_die, "cu_start", 0) if context_die is not None else 0
                off += int(base or 0)
        except Exception:
            pass
        return off

    # The cache lives per-instance because "self" participates in the key.
    @lru_cache(maxsize=8192)
    def get_die(self, offset: int) -> model.DebugInformationEntry | None:
        """Retrieve DIE by absolute offset with LRU caching.

        Args:
            offset: Absolute DIE offset (not CU-relative)

        Returns:
            DebugInformationEntry if found, None otherwise

        Note:
            Cache is per-instance (8K entries) to minimize SQLAlchemy query overhead.
        """
        return self.session.query(model.DebugInformationEntry).filter_by(offset=offset).one_or_none()

    def traverse_tree(self, entry: model.DebugInformationEntry, level: int = 0) -> None:
        """Traverse DIE tree depth-first, printing formatted summaries.

        Prints context-aware summaries for common DIE types:
            - **variable**: Shows name, type, and location expression
            - **enumerator**: Shows name, type, and constant value
            - **subrange_type**: Shows array bounds (lower_bound, upper_bound)
            - **member**: Shows struct member name, type, and offset
            - **base_type**: Shows size and encoding (e.g., "4 bytes - signed")

        Args:
            entry: Root DIE to start traversal
            level: Current indentation level (default: 0)

        Example:
            ```python
            root = session.query(DebugInformationEntry).first()
            parser.traverse_tree(root)
            # Output:
            # variable 'global_counter' -> uint32_t [location=addr(0x20000000)] [off=0x00001234]
            #     base_type 'uint32_t' [4 bytes - unsigned] [off=0x00001100]
            ```

        Note:
            Type references are automatically resolved and displayed.
            Indentation increases by 4 spaces per level.
        """
        tag = getattr(entry.abbrev, "tag", entry.tag)
        name = self._name_of(entry)
        type_info = ""
        # Resolve type summary with proper CU-relative adjustment for ref forms
        attr = self._get_attr(entry, "type")
        if attr is not None:
            raw = getattr(attr, "raw_value", None)
            try:
                off = int(raw) if raw is not None else None
            except Exception:
                off = None
            if off is not None:
                try:
                    frm = getattr(attr, "form", None)
                    if frm in (
                        getattr(AttributeForm, "DW_FORM_ref1", None),
                        getattr(AttributeForm, "DW_FORM_ref2", None),
                        getattr(AttributeForm, "DW_FORM_ref4", None),
                        getattr(AttributeForm, "DW_FORM_ref8", None),
                        getattr(AttributeForm, "DW_FORM_ref_udata", None),
                    ):
                        base = getattr(entry, "cu_start", 0) or 0
                        off += int(base)
                except Exception:
                    pass
                type_info = f" -> {self._type_summary(int(off))}"
        if "location" in entry.attributes_map:
            location = self.dwarf_expression(entry.attributes_map["location"].form, entry.attributes_map["location"].raw_value)
            print(f"{'    ' * level}{tag} '{name}'{type_info} [location={location}] [off=0x{entry.offset:08x}]")
        else:
            if tag == "enumerator" and "const_value" in entry.attributes_map:
                enumerator_value = int(entry.attributes_map["const_value"].raw_value)
                print(f"{'    ' * level}{tag} '{name}'{type_info} [value={enumerator_value}] [off=0x{entry.offset:08x}]")
            elif tag == "subrange_type":
                lower_bound = 0
                upper_bound = 0
                if "lower_bound" in entry.attributes_map:
                    lower_bound = int(entry.attributes_map["lower_bound"].raw_value)
                if "upper_bound" in entry.attributes_map:
                    upper_bound = int(entry.attributes_map["upper_bound"].raw_value)
                print(
                    f"{'    ' * level}{tag} '{name}'{type_info} [lower_bound={lower_bound}: upper_bound={upper_bound}] [off=0x{entry.offset:08x}]"
                )
            elif tag == "member" and "data_member_location" in entry.attributes_map:
                data_member_location = self.dwarf_expression(
                    entry.attributes_map["data_member_location"].form, entry.attributes_map["data_member_location"].raw_value
                )
                print(f"{'    ' * level}{tag} '{name}'{type_info} [location={data_member_location}] [off=0x{entry.offset:08x}]")
            elif tag == "base_type":
                descr = ""
                if "byte_size" in entry.attributes_map:
                    byte_size = int(entry.attributes_map["byte_size"].raw_value)
                    descr = f"{byte_size} bytes"
                if "encoding" in entry.attributes_map:
                    encoding = BaseTypeEncoding(int(entry.attributes_map["encoding"].raw_value)).name
                    descr += f" - {encoding}"
                if descr:
                    descr = f"[{descr}]"
                print(f"{'    ' * level}{tag} '{name}'{type_info} {descr} [off=0x{entry.offset:08x}]")
            else:
                print(f"{'    ' * level}{tag} '{name}'{type_info} [off=0x{entry.offset:08x}]")

        for child in getattr(entry, "children", []) or []:
            self.traverse_tree(child, level + 1)

    @lru_cache(maxsize=8192)
    def parse_attributes(self, die: model.DebugInformationEntry, level: int) -> dict[str, Any]:
        """Parse DIE attributes into dictionary with type conversion and resolution.

        Extracts attributes from a DIE with special handling for:
            - **type**: Recursively resolves to complete type tree
            - **location/data_member_location**: Evaluates DWARF expressions
            - **Enum attributes**: Converts to enum values (encoding, language, etc.)
            - **CU-relative refs**: Adjusts to absolute offsets

        Attributes in STOP_LIST are excluded (sibling, decl_file, decl_line, etc.).

        Args:
            die: Debug Information Entry to parse
            level: Current recursion depth (for nested type resolution)

        Returns:
            Dict mapping attribute names to converted values.
            Type attributes contain nested DIE objects.

        Example:
            ```python
            attrs = parser.parse_attributes(die, 0)
            # Result:
            # {
            #     "name": "my_var",
            #     "type": DIE(tag="base_type", attributes={"byte_size": 4}),
            #     "location": "addr(0x20000000)"
            # }
            ```

        Note:
            Results are LRU-cached (8K entries) per instance.
        """
        result: dict[str, Any] = defaultdict(dict)
        # Prefer attributes_map to avoid repeated scans
        attrs_map = getattr(die, "attributes_map", None)
        if attrs_map is None:
            # Fallback if attribute map is not available
            attrs_iter = ((a.name, a) for a in (die.attributes or []))
        else:
            attrs_iter = attrs_map.items()

        for attr_name, attr in attrs_iter:
            if attr_name in self.STOP_LIST:
                continue

            self.att_types[getattr(die.abbrev, "tag", die.tag)].add(attr_name)

            # Handle type-like references
            if attr_name == "type":
                try:
                    referenced_offset = int(attr.raw_value)
                except Exception:
                    referenced_offset = None
                if referenced_offset is not None:
                    # Adjust CU-relative reference forms to absolute DIE offsets
                    try:
                        frm = getattr(attr, "form", None)
                        if frm in (
                            getattr(AttributeForm, "DW_FORM_ref1", None),
                            getattr(AttributeForm, "DW_FORM_ref2", None),
                            getattr(AttributeForm, "DW_FORM_ref4", None),
                            getattr(AttributeForm, "DW_FORM_ref8", None),
                            getattr(AttributeForm, "DW_FORM_ref_udata", None),
                        ):
                            base = getattr(die, "cu_start", 0) or 0
                            referenced_offset += int(base)
                    except Exception:
                        pass
                if referenced_offset and referenced_offset != die.offset:
                    # result.setdefault("attrs", {})[attr_name] = self.parse_type(referenced_offset, level + 1)
                    result[attr_name] = self.parse_type(referenced_offset, level + 1)
                    continue
            # Default: keep raw_value to stay close to DB content
            # result.setdefault("attrs", {})[attr_name] = attr.raw_value
            elif attr_name in DATA_REPRESENTATION:
                converter = DATA_REPRESENTATION[attr_name]
                try:
                    attr_value = int(attr.raw_value)
                except Exception:
                    result[attr_name] = attr.raw_value
                    continue
                try:
                    converted_value = converter(attr_value)
                except Exception:
                    converted_value = attr_value
                result[attr_name] = converted_value
            elif attr_name in ("location", "data_member_location", "vtable_elem_location"):
                result[attr_name] = self.dwarf_expression(attr.form, attr.raw_value)
            else:
                result[attr_name] = attr.raw_value
        return result

    def parse_type(self, offset: int, level: int = 0) -> dict[str, Any] | CircularReference:
        """Recursively parse DWARF type DIE into structured representation.

        Follows type references to build complete type descriptions with attributes
        and children. Detects circular references (e.g., linked list nodes) and
        returns CircularReference marker to prevent infinite recursion.

        Args:
            offset: Absolute DIE offset of the type
            level: Current recursion depth (unused but kept for compatibility)

        Returns:
            DIE object with:
                - **tag**: DWARF tag name (e.g., "base_type", "pointer_type")
                - **attributes**: Dict of converted attribute values
                - **children**: List of child DIE objects (members, enumerators, etc.)

            OR CircularReference if a cycle is detected.

        Example:
            ```python
            # Parse struct type
            type_die = parser.parse_type(0x1234)
            print(type_die.tag)  # "structure_type"
            print(type_die.attributes["name"])  # "my_struct"
            for member in type_die.children:
                print(f"  {member.attributes['name']}: {member.attributes['type'].tag}")
            ```

        Note:
            Results are cached in self.parsed_types dict.
            CU-relative type references are automatically adjusted.
        """
        # Cycle detection
        if offset in self.type_stack:
            # Try to enrich with name where possible
            name_val = ""
            die = self.get_die(offset)
            if die is not None:
                # Use attributes_map for quick access
                name_attr = getattr(die, "attributes_map", {}).get("name") if hasattr(die, "attributes_map") else None
                if name_attr is None:
                    # fallback scan
                    for a in die.attributes or []:
                        if a.name == "name":
                            name_attr = a
                            break
                if name_attr is not None:
                    try:
                        name_val = str(name_attr.raw_value)
                    except Exception:
                        name_val = ""
            return CircularReference(tag=(die.abbrev.tag if die else ""), name=name_val)

        # Memoized?
        if offset in self.parsed_types:
            return self.parsed_types[offset]

        die = self.get_die(offset)
        if die is None:
            return {"tag": "<missing>", "attrs": {}}

        self.type_stack.add(offset)
        try:
            # result: dict[str, Any] = defaultdict(dict)
            # result["tag"] = getattr(die.abbrev, "tag", die.tag)
            # result["children"] = []

            result: DIE = DIE(getattr(die.abbrev, "tag", die.tag))

            # Parse this DIE's attributes
            result.attributes.update(self.parse_attributes(die, level))

            # Parse interesting children (e.g., members of a struct, enumerators, subrange bounds)
            for child in getattr(die, "children", []) or []:
                # sub: dict[str, Any] = defaultdict(dict)
                # sub["tag"] = getattr(child.abbrev, "tag", child.tag)
                sub: DIE = DIE(getattr(child.abbrev, "tag", child.tag))
                sub.attributes.update(self.parse_attributes(child, level + 1))
                result.children.append(sub)

            # cache result
            self.parsed_types[offset] = result
            return result
        finally:
            self.type_stack.remove(offset)

    # --- Helpers for summaries -------------------------------------------------
    def _get_attr(self, die: model.DebugInformationEntry, name: str):
        """Get attribute by name from DIE, preferring attributes_map.

        Args:
            die: Debug Information Entry
            name: Attribute name to retrieve

        Returns:
            DIEAttribute if found, None otherwise
        """
        if hasattr(die, "attributes_map"):
            return die.attributes_map.get(name)
        for a in die.attributes or []:
            if a.name == name:
                return a
        return None

    def _attr_raw(self, die: model.DebugInformationEntry, name: str):
        """Get raw attribute value by name.

        Args:
            die: Debug Information Entry
            name: Attribute name

        Returns:
            Attribute's raw_value if found, None otherwise
        """
        a = self._get_attr(die, name)
        return None if a is None else a.raw_value

    def _name_of(self, die: model.DebugInformationEntry) -> str:
        """Extract name attribute from DIE, returning empty string if not found.

        Args:
            die: Debug Information Entry

        Returns:
            Name as string, or empty string if unavailable
        """
        try:
            return self._attr_raw(die, "name") or ""
        except Exception:
            return ""

    def _type_summary(self, offset: int) -> str:
        """Generate concise human-readable summary for a type DIE.

        Args:
            offset: Absolute DIE offset of type

        Returns:
            Type name if available, otherwise tag name (e.g., "uint32_t" or "base_type")
            Returns "<missing type at 0x...>" if DIE not found.

        Example:
            ```python
            summary = parser._type_summary(0x1234)
            # "uint32_t" or "structure_type" or "pointer_type"
            ```
        """
        die = self.get_die(offset)
        if die is None:
            return f"<missing type at 0x{offset:08x}>"
        tag = getattr(die.abbrev, "tag", die.tag)
        name = self._name_of(die)
        return name or tag
