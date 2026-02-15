"""DWARF Debugging Information Entry (DIE) attribute parser with optimized caching.

This module provides high-performance parsing and traversal of DWARF DIE trees,
with specialized support for type reference resolution and circular reference detection.

The AttributeParser implements a three-tier caching strategy:
    1. **parsed_types**: Per-instance memoization of fully parsed type dictionaries
    2. **get_die()**: LRU-cached DIE lookups by CU-relative offset (reduces ORM overhead)
    3. **type_stack**: Cycle detection to handle self-referential type definitions

Key Features:
    - Depth-first DIE tree traversal with intelligent caching
    - Domain-specific formatting for common DIE tags (variables, typedefs, subprograms)
    - Recursive type parsing with circular reference detection
    - Leverages ORM-side attributes_map when available for performance

Architecture:
    The parser operates in two modes:

    1. **Tree Traversal** (traverse_tree):
       - Walks the DIE tree depth-first
       - Prints formatted summaries for each DIE
       - Automatically parses and caches type DIEs on-demand
       - Tracks visited DIEs to avoid redundant processing

    2. **Type Parsing** (parse_type):
       - Recursively resolves type references
       - Handles pointer types, struct/union members, arrays, typedefs
       - Returns structured dictionaries with tag, attrs, and children
       - Returns CircularReference marker for self-referential types

Type Reference Resolution:
    Type references are encoded as CU-relative DIE offsets in the "type" attribute.
    The parser follows these references recursively, building a complete type graph
    while detecting and breaking cycles.

Example Usage:
    ```python
    from objutils.elf import ElfParser
    from objutils.dwarf import DwarfProcessor
    from objutils.dwarf.attrparser import AttributeParser, traverse_dict

    # Parse ELF and extract DWARF debug info
    ep = ElfParser("firmware.elf")
    dp = DwarfProcessor(ep)
    dp.do_dbg_info()

    # Create parser and traverse DIE tree
    session = ep.session
    root = session.query(model.DebugInformationEntry).first()
    ap = AttributeParser(session)
    ap.traverse_tree(root)

    # Parse specific type by offset
    type_dict = ap.parse_type(0x1234)
    traverse_dict(type_dict)  # Pretty-print the type structure
    ```

Performance Considerations:
    - LRU cache size of 8192 for DIE lookups (adjustable via maxsize parameter)
    - Attributes are filtered via STOP_LIST to exclude non-structural metadata
    - Visited set prevents redundant traversal of shared subtrees
    - attributes_map provides O(1) attribute access when available

ORM Schema Requirements:
    The parser expects DebugInformationEntry with:
    - offset: CU-relative DIE offset (int)
    - tag: DIE tag name (str)
    - abbrev.tag: Abbreviation-based tag access
    - attributes: List of DIEAttribute objects
    - attributes_map: Dict mapping attribute names to DIEAttribute (optional, performance)
    - children: List of child DIEs
    - parent: Parent DIE reference

DIEAttribute Schema:
    - name: Attribute name (str)
    - raw_value: Decoded attribute value (int, str, bytes, etc.)

Note:
    Type references are assumed to be CU-relative offsets stored as integers
    in DIEAttribute.raw_value for the "type" attribute and similar references.

See Also:
    - objutils.dwarf.c_generator: Generates C code from parsed DIE trees
    - objutils.dwarf.traverser: Alternative DIE tree walker
    - objutils.elf.model: SQLAlchemy ORM definitions for DWARF DIEs
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from objutils.elf import model


def lev_print(level: int, *args: Any, **kws: Any) -> None:
    """Print with indentation based on nesting level.

    Args:
        level: Indentation level (each level = 4 spaces)
        *args: Positional arguments passed to print()
        **kws: Keyword arguments passed to print()
    """
    print("    " * level, *args, **kws)


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
    """

    tag: str
    name: str


class AttributeParser:
    """Parse and traverse DWARF DIE trees with optimized caching and type resolution.

    This parser provides efficient traversal of DWARF Debugging Information Entry (DIE)
    trees with intelligent caching of parsed types and DIE lookups. It handles circular
    type references, follows type chains, and produces structured representations of
    complex types (structs, unions, arrays, pointers, etc.).

    Caching Strategy:
        - **parsed_types**: Memoizes fully parsed type dictionaries by DIE offset
          (prevents re-parsing the same type multiple times)
        - **get_die()**: LRU cache (8192 entries) for DIE lookups by offset
          (minimizes SQLAlchemy ORM query overhead)
        - **visited_die_offsets**: Tracks already-traversed DIEs during tree walks
          (avoids redundant processing of shared subtrees)
        - **type_stack**: Runtime cycle detection for recursive type references
          (prevents infinite recursion)

    Attribute Filtering:
        Non-structural attributes in STOP_LIST (decl_file, decl_line, decl_column,
        sibling) are excluded from parsed type dictionaries to keep output focused
        on semantic type information.

    Type Parsing:
        The parse_type() method recursively follows "type" attribute references,
        building a nested dictionary structure:
        ```python
        {
            "tag": "pointer_type",
            "attrs": {"byte_size": 8, "type": {...}},
            "children": []
        }
        ```

    Tree Traversal:
        The traverse_tree() method walks DIE trees depth-first, printing formatted
        summaries with special handling for common DIE types (variables, functions,
        typedefs, constants).

    Attributes:
        session: SQLAlchemy session for ORM queries
        type_stack: Set of offsets currently being parsed (cycle detection)
        parsed_types: Cache of offset -> parsed type dict
        visited_die_offsets: Set of DIE offsets already traversed
        att_types: Statistics dict mapping tag -> set of attribute names encountered

    Example:
        ```python
        from objutils.dwarf.attrparser import AttributeParser

        ap = AttributeParser(session)

        # Traverse entire DIE tree with summaries
        root_die = session.query(DebugInformationEntry).first()
        ap.traverse_tree(root_die)

        # Parse specific type
        type_dict = ap.parse_type(0x1234)
        if isinstance(type_dict, CircularReference):
            print("Circular reference detected")
        else:
            print(f"Type: {type_dict['tag']}")
        ```

    Note:
        This parser expects the ORM schema from objutils.elf.model with
        DebugInformationEntry, DIEAttribute, and optionally attributes_map
        for performance optimization.
    """

    # Attributes considered non-structural for high-level type dicts
    STOP_LIST: set[str] = {
        "decl_file",
        "decl_line",
        "decl_column",
        "sibling",
    }

    def __init__(self, session):
        """Initialize AttributeParser with SQLAlchemy session.

        Args:
            session: SQLAlchemy session connected to ELF ORM database
        """
        self.session = session
        # Used to detect cycles while descending type links
        self.type_stack: set[int] = set()
        # Parsed type cache: offset -> structured dict
        self.parsed_types: dict[int, dict[str, Any]] = {}
        # DIEs already processed by traverse_tree to avoid redundant work
        self.visited_die_offsets: set[int] = set()
        # Tag -> set(attributes encountered) for insights/statistics
        self.att_types: dict[str, set[str]] = defaultdict(set)

    # LRU cache on a helper method to lookup DIEs by offset.
    # The cache lives per-instance because "self" participates in the key.
    @lru_cache(maxsize=8192)
    def get_die(self, offset: int) -> model.DebugInformationEntry | None:
        """Retrieve DIE by CU-relative offset with LRU caching.

        This method wraps SQLAlchemy queries with an LRU cache to minimize
        database overhead during type reference resolution. The cache is
        per-instance and holds up to 8192 entries.

        Args:
            offset: CU-relative DIE offset (integer)

        Returns:
            DebugInformationEntry if found, None otherwise

        Note:
            The cache key includes self, so each AttributeParser instance
            maintains its own independent cache.
        """
        return self.session.query(model.DebugInformationEntry).filter(model.DebugInformationEntry.offset == offset).first()

    # --- Helpers for summaries -------------------------------------------------
    def _get_attr(self, die: model.DebugInformationEntry, name: str):
        """Get attribute by name from DIE, preferring attributes_map if available.

        Args:
            die: Debug Information Entry
            name: Attribute name to retrieve

        Returns:
            DIEAttribute if found, None otherwise
        """
        amap = getattr(die, "attributes_map", None)
        if amap is not None:
            return amap.get(name)
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
        a = self._get_attr(die, "name")
        try:
            return str(a.raw_value) if a is not None and a.raw_value is not None else ""
        except Exception:
            return ""

    def _type_summary(self, offset: int) -> str:
        """Generate human-readable summary for a type DIE.

        Args:
            offset: CU-relative offset of type DIE

        Returns:
            Type name or tag (e.g., "uint32_t" or "pointer_type")

        Note:
            This method is defensive and returns fallback strings on any error.
        """
        try:
            t = self.parse_type(offset)
        except Exception:
            return f"<type@0x{offset:08x}>"
        if not isinstance(t, dict):
            # CircularReference or other marker
            try:
                return f"{getattr(t, 'tag', '')}({getattr(t, 'name', '')})"
            except Exception:
                return f"<type@0x{offset:08x}>"
        tag = t.get("tag", "<type>")
        name = ""
        attrs = t.get("attrs", {}) if isinstance(t.get("attrs"), dict) else {}
        if "name" in attrs and attrs["name"]:
            try:
                name = str(attrs["name"])
            except Exception:
                name = ""
        return name or tag

    def traverse_tree(self, entry: model.DebugInformationEntry, level: int = 0) -> None:
        """Traverse DIE tree depth-first, printing formatted summaries.

        This method walks the DIE tree recursively, printing domain-specific
        summaries for common DIE types (variables, typedefs, functions, constants).
        Type DIEs are automatically parsed and cached on-demand.

        Special handling for:
            - **variable**: Shows name, type, and location
            - **typedef**: Shows alias name and target type
            - **constant**: Shows name, type, and value
            - **subprogram**: Shows function signature with parameters

        Args:
            entry: Root DIE to start traversal
            level: Current indentation level (default: 0)

        Note:
            Already-visited DIEs are skipped to avoid redundant processing.
            Parsed types are cached in self.parsed_types.
        """
        # Skip if already visited to avoid redundant work
        if entry.offset in self.visited_die_offsets:
            return
        self.visited_die_offsets.add(entry.offset)

        tag = entry.abbrev.tag if hasattr(entry, "abbrev") else entry.tag
        lev_print(level, f"Tag: {tag}")

        # If this is a type that's already been parsed, we can stop here.
        # The summary calls above will use the cached version.
        if tag.endswith("_type") and entry.offset in self.parsed_types:
            # Optional: print a note that we're using a cached type
            lev_print(level + 1, f"(Using cached type for offset {entry.offset})")
            return

        # Domain-specific summaries for common DIE kinds
        if tag == "variable":
            nm = self._name_of(entry)
            type_off = self._attr_raw(entry, "type")
            type_desc = self._type_summary(int(type_off)) if isinstance(type_off, (int,)) else "<unknown>"
            loc = self._attr_raw(entry, "location")
            lev_print(level + 1, f"Variable: {nm or '<anon>'} : {type_desc}" + (" @" + str(loc) if loc is not None else ""))
        elif tag == "typedef":
            nm = self._name_of(entry)
            type_off = self._attr_raw(entry, "type")
            type_desc = self._type_summary(int(type_off)) if isinstance(type_off, (int,)) else "<unknown>"
            lev_print(level + 1, f"Typedef: {nm or '<anon>'} = {type_desc}")
        elif tag == "constant":
            nm = self._name_of(entry)
            type_off = self._attr_raw(entry, "type")
            type_desc = self._type_summary(int(type_off)) if isinstance(type_off, (int,)) else "<unknown>"
            cval = self._attr_raw(entry, "const_value")
            lev_print(level + 1, f"Constant: {nm or '<anon>'} : {type_desc} = {cval}")
        elif tag == "subprogram":
            nm = self._name_of(entry)
            rtoff = self._attr_raw(entry, "type")
            rtdesc = self._type_summary(int(rtoff)) if isinstance(rtoff, (int,)) else "void"
            lev_print(level + 1, f"Subprogram: {nm or '<anon>'}() -> {rtdesc}")
            # Print a short parameter list summary
            try:
                for ch in getattr(entry, "children", []) or []:
                    ctag = ch.abbrev.tag if hasattr(ch, "abbrev") else ch.tag
                    if ctag == "formal_parameter":
                        pn = self._name_of(ch)
                        ptoff = self._attr_raw(ch, "type")
                        ptdesc = self._type_summary(int(ptoff)) if isinstance(ptoff, (int,)) else "<unknown>"
                        lev_print(level + 2, f"param: {pn or '<anon>'} : {ptdesc}")
            except Exception:
                pass

        # Print attributes (already decoded by DWARF pass)
        for attr in entry.attributes:
            lev_print(level + 1, f"Attribute: {attr.name} = {attr.raw_value}")

        # If this DIE is itself a type or typedef/subrange etc., parse it once
        if tag == "type" or tag.endswith("_type") or tag in ("typedef", "subrange_type"):
            # For a type DIE, entry.offset should identify this DIE for parse_type
            try:
                tp = self.parse_type(entry.offset, level + 1)
                traverse_dict(tp, level + 1)
            except Exception:
                # Defensive: never let printing a type break the traversal
                pass

        # Recurse into children
        for child in getattr(entry, "children", []) or []:
            self.traverse_tree(child, level + 1)

    def parse_attributes(self, die: model.DebugInformationEntry, level: int) -> dict[str, Any]:
        """Parse DIE attributes into structured dictionary.

        Extracts attributes from a DIE, filtering out non-structural metadata
        (decl_file, decl_line, etc.) and recursively resolving "type" references.

        Args:
            die: Debug Information Entry to parse
            level: Current nesting level for recursive type parsing

        Returns:
            Dictionary with "attrs" key containing attribute name -> value mappings.
            Type references are recursively resolved to nested dictionaries.

        Note:
            Attributes in STOP_LIST are excluded. The "type" attribute triggers
            recursive parse_type() calls to follow type chains.
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
                if referenced_offset and referenced_offset != die.offset:
                    result.setdefault("attrs", {})[attr_name] = self.parse_type(referenced_offset, level + 1)
                    continue

            # Default: keep raw_value to stay close to DB content
            result.setdefault("attrs", {})[attr_name] = attr.raw_value

        return result

    def parse_type(self, offset: int, level: int = 0) -> dict[str, Any] | CircularReference:
        """Recursively parse DWARF type DIE into structured dictionary.

        Follows type references to build complete type representations, handling
        pointers, structs, unions, arrays, typedefs, and other DWARF type constructs.
        Detects circular references and returns CircularReference marker to prevent
        infinite recursion.

        Args:
            offset: CU-relative DIE offset of the type
            level: Current recursion depth (for debugging)

        Returns:
            Dictionary with keys:
                - "tag": DWARF tag name (e.g., "pointer_type", "structure_type")
                - "attrs": Dict of attribute name -> value (type refs are recursively parsed)
                - "children": List of child DIE dicts (e.g., struct members, enumerators)

            OR CircularReference if a cycle is detected.

        Raises:
            None: Defensively handles missing DIEs and parse errors

        Example:
            ```python
            # Parse a struct type
            type_dict = parser.parse_type(0x1234)
            # Result:
            # {
            #     "tag": "structure_type",
            #     "attrs": {"name": "foo", "byte_size": 16},
            #     "children": [
            #         {"tag": "member", "attrs": {"name": "x", "type": {...}}},
            #         {"tag": "member", "attrs": {"name": "y", "type": {...}}}
            #     ]
            # }
            ```

        Note:
            Results are cached in self.parsed_types. Circular references
            (e.g., linked list nodes) return CircularReference marker.
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
            result: dict[str, Any] = defaultdict(dict)
            result["tag"] = getattr(die.abbrev, "tag", die.tag)
            result["children"] = []

            # Parse this DIE's attributes
            result.update(self.parse_attributes(die, level))

            # Parse interesting children (e.g., members of a struct, enumerators, subrange bounds)
            for child in getattr(die, "children", []) or []:
                sub: dict[str, Any] = defaultdict(dict)
                sub["tag"] = getattr(child.abbrev, "tag", child.tag)
                sub.update(self.parse_attributes(child, level + 1))
                result["children"].append(sub)

            # cache result
            self.parsed_types[offset] = result
            return result
        finally:
            self.type_stack.remove(offset)


def traverse_dict(elem: dict[str, Any], level: int = 0) -> None:
    """Pretty-print a parsed type dictionary recursively.

    Formats and prints a structured type dictionary from parse_type(),
    displaying tags, attributes, and children with proper indentation.

    Args:
        elem: Type dictionary from AttributeParser.parse_type()
        level: Current indentation level

    Example:
        ```python
        type_dict = parser.parse_type(0x1234)
        traverse_dict(type_dict)
        # Output:
        # *** tag: structure_type
        #     name ==> my_struct
        #     byte_size ==> 16
        #     *** tag: member
        #         name ==> field1
        #         ...
        ```
    """
    lev_print(level, f"*** tag: {elem.get('tag')}")

    # 1) Attributes
    attrs = elem.get("attrs")
    if isinstance(attrs, dict):
        for k, v in attrs.items():
            if isinstance(v, dict):
                traverse_dict(v, level + 1)
            elif isinstance(v, CircularReference):
                lev_print(level + 1, f"{k} ==> CircularRef(tag={v.tag}, name={v.name})")
            else:
                lev_print(level + 1, f"{k} ==> {v}")

    # 2) Children
    children = elem.get("children")
    if isinstance(children, list):
        for child in children:
            traverse_dict(child, level + 1)
