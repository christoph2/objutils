"""C/C++ code generator from DWARF debugging information.

This module generates C/C++ header files from DWARF DIE (Debug Information Entry)
trees, reconstructing type declarations, variable declarations, and function prototypes.
Uses Mako templates for flexible rendering.

The generator builds on AttributeParser to extract structured type information and
render it as valid C/C++ syntax. It handles:
    - **Typedefs**: Type aliases
    - **Enumerations**: Named integer constants with optional explicit values
    - **Structures/Classes**: Composite types with members and optional inheritance
    - **Unions**: Overlapping member storage
    - **Variables**: Global/static variable declarations (extern)
    - **Functions**: Function prototypes with typed parameters

Design Goals:
    - Keep caching and logic localized (no schema modifications)
    - Use inline Mako templates (minimize file churn)
    - Support anonymous inline types (unnamed struct/union/enum members)
    - Handle complex type specifications (pointers, arrays, qualifiers)
    - Generate valid, compilable C code

Architecture:
    The generator operates in two phases:
    
    1. **Declaration Collection** (generate_declarations):
       - Walks DIE tree recursively
       - Normalizes each DIE into a dict structure suitable for templates
       - Groups declarations by category (typedefs, enums, records, unions, etc.)
       - Caches results per DIE offset to avoid redundant processing
    
    2. **Code Rendering** (generate_header):
       - Applies Mako templates to normalized declarations
       - Handles include guards and formatting
       - Produces complete C header file

Type Rendering:
    Complex types are rendered with special attention to:
    - **Pointers**: `int *`, `void *`, `const char *`
    - **Arrays**: Single and multi-dimensional with explicit sizes
    - **Qualifiers**: `const`, `volatile`, `restrict`
    - **References**: C++ `&` and `&&` references
    - **Anonymous types**: Inline struct/union/enum definitions

Usage Example:
    ```python
    from objutils.elf import ElfParser
    from objutils.dwarf import DwarfProcessor
    from objutils.dwarf.c_generator import CGenerator

    # Parse ELF and import DWARF
    ep = ElfParser("firmware.elf")
    dp = DwarfProcessor(ep)
    dp.do_dbg_info()

    # Generate C header
    session = ep.session
    root = session.query(DebugInformationEntry).first()
    gen = CGenerator(session)
    code = gen.generate_header(root, "firmware.h")
    
    # Write to file
    with open("generated.h", "w") as f:
        f.write(code)
    ```

Advanced Usage:
    ```python
    from objutils.dwarf.c_generator import CGenerator, RenderOptions

    # Custom rendering options
    opts = RenderOptions(
        language="c",
        indent="  ",  # 2 spaces instead of 4
        include_guards=True,
        header_guard="MY_CUSTOM_GUARD_H"
    )
    gen = CGenerator(session, options=opts)
    
    # Generate with custom AttributeParser
    from objutils.dwarf.traverser import AttributeParser
    ap = AttributeParser(session)
    gen = CGenerator(session, attribute_parser=ap, options=opts)
    ```

Template Variables:
    The Mako template receives these variables:
    - **guard**: Include guard macro name (or None)
    - **typedefs**: List of typedef dicts with 'name' and 'target'
    - **enums**: List of enum dicts with 'name' and 'items' [(name, value), ...]
    - **records**: List of struct/class dicts with 'name' and 'members'
    - **unions**: List of union dicts with 'name' and 'members'
    - **variables**: List of variable dicts with 'name' and 'type'
    - **functions**: List of function dicts with 'name', 'returns', and 'params'
    - **opt**: RenderOptions instance

Member Dict Structure:
    Each member dict contains:
    - **name**: Member name (str)
    - **type**: Full type string (e.g., "const int *")
    - **type_head**: Type without array dimensions (e.g., "const int *")
    - **type_suffix**: Array dimensions (e.g., "[10][20]")
    - **inline**: True if this is an anonymous inline type
    - **inline_kind**: "struct", "union", or "enum" (if inline)
    - **inline_members**: List of nested member dicts (if struct/union)
    - **inline_items**: List of (name, value) tuples (if enum)

Performance Considerations:
    - DIE offset-based caching prevents redundant processing
    - LRU cache on _split_type_desc (16K entries)
    - AttributeParser caching reused for type resolution

Limitations:
    - C++ features (inheritance, templates, namespaces) are simplified
    - Bitfield members are not yet supported
    - Function pointer types may need manual adjustment
    - Inline assembly and compiler attributes are omitted

See Also:
    - objutils.dwarf.traverser: AttributeParser for type resolution
    - objutils.dwarf.attrparser: Alternative DIE traverser
    - Mako Templates: https://www.makotemplates.org/
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from mako.template import Template

from objutils.dwarf.traverser import AttributeParser
from objutils.elf import model


@dataclass
class RenderOptions:
    """Configuration options for C code generation.

    Attributes:
        language: Target language ("c" or "c++", reserved for future)
        indent: Indentation string (default: 4 spaces)
        include_guards: Whether to generate include guards
        header_guard: Custom include guard macro name (auto-generated if None)

    Example:
        ```python
        opts = RenderOptions(
            language="c",
            indent="  ",  # 2 spaces
            include_guards=True,
            header_guard="MY_HEADER_H"
        )
        gen = CGenerator(session, options=opts)
        ```
    """

    language: str = "c"  # or "c++" (reserved for future)
    indent: str = "    "
    include_guards: bool = True
    header_guard: str | None = None


class CGenerator:
    """Generate C/C++ header files from DWARF debugging information.

    This class walks DWARF DIE trees and generates valid C code including type
    definitions, variable declarations, and function prototypes. It leverages
    AttributeParser for type resolution and uses Mako templates for rendering.

    The generator maintains per-DIE caching to avoid redundant processing of
    complex type trees. Each DIE is normalized into a template-friendly dict
    structure before rendering.

    Attributes:
        session: SQLAlchemy session for ORM queries
        ap: AttributeParser instance for type resolution
        options: RenderOptions controlling output formatting
        _decls_cache: Cache mapping DIE offset -> normalized declarations dict

    Example:
        ```python
        # Basic usage
        gen = CGenerator(session)
        code = gen.generate_header(root_die, "my_types.h")
        
        # With custom options
        opts = RenderOptions(indent="  ", header_guard="CUSTOM_H")
        gen = CGenerator(session, options=opts)
        
        # With pre-existing AttributeParser
        ap = AttributeParser(session)
        gen = CGenerator(session, attribute_parser=ap)
        ```

    Note:
        The generator skips anonymous types at top level (e.g., unnamed structs)
        but includes them inline when used as struct members.
    """

    def __init__(self, session, attribute_parser: AttributeParser | None = None, options: RenderOptions | None = None):
        """Initialize CGenerator.

        Args:
            session: SQLAlchemy session connected to DWARF database
            attribute_parser: Optional pre-configured AttributeParser (creates new if None)
            options: Optional RenderOptions (uses defaults if None)
        """
        self.session = session
        self.ap = attribute_parser or AttributeParser(session)
        self.options = options or RenderOptions()
        # Cache for expensive per-DIE computations
        self._decls_cache: dict[int, dict[str, list[dict[str, Any]]]] = {}

    # ------------- Public API -------------------------------------------------
    def generate_header(self, start_die: model.DebugInformationEntry, header_name: str | None = None) -> str:
        """Generate complete C header file from DIE tree.

        Args:
            start_die: Root DIE to start traversal (typically compilation unit)
            header_name: Optional header filename for include guard generation

        Returns:
            Complete C header file as string with include guards and declarations

        Example:
            ```python
            root = session.query(DebugInformationEntry).first()
            code = gen.generate_header(root, "firmware.h")
            print(code)
            # Output:
            # #ifndef _FIRMWARE_H_
            # #define _FIRMWARE_H_
            # /* Generated by objutils.dwarf.c_generator using DWARF DIEs */
            # ...
            # #endif /* _FIRMWARE_H_ */
            ```
        """
        decls = self.generate_declarations(start_die)
        hdr_guard = self._guard_name(header_name) if self.options.include_guards else None
        return self._render_header(decls, hdr_guard)

    def generate_declarations(self, start_die: model.DebugInformationEntry) -> dict[str, list[dict[str, Any]]]:
        """Traverse DIE subtree and collect normalized declarations grouped by category.

        Walks the DIE tree recursively and extracts all type definitions, variables,
        and function prototypes. Anonymous types are skipped at top level but included
        inline when referenced.

        Args:
            start_die: Root DIE to start traversal

        Returns:
            Dict with keys:
                - "typedefs": List of typedef dicts
                - "enums": List of enum dicts
                - "records": List of struct/class dicts
                - "unions": List of union dicts
                - "variables": List of variable dicts
                - "functions": List of function prototype dicts

        Example:
            ```python
            decls = gen.generate_declarations(root_die)
            print(f"Found {len(decls['typedefs'])} typedefs")
            print(f"Found {len(decls['enums'])} enums")
            print(f"Found {len(decls['records'])} structs")
            ```

        Note:
            Results are cached by DIE offset. Multiple calls with the same DIE
            return cached results immediately.
        """
        # Use DIE offset as a stable cache key when available
        key = getattr(start_die, "offset", None)
        if isinstance(key, int) and key in self._decls_cache:
            return self._decls_cache[key]

        typedefs: list[dict[str, Any]] = []
        enums: list[dict[str, Any]] = []
        records: list[dict[str, Any]] = []  # struct/class
        unions: list[dict[str, Any]] = []
        variables: list[dict[str, Any]] = []
        functions: list[dict[str, Any]] = []

        def walk(die: model.DebugInformationEntry):
            tag = getattr(die.abbrev, "tag", die.tag)
            if tag == "typedef":
                typedefs.append(self._normalize_typedef(die))
            elif tag == "enumeration_type":
                e = self._normalize_enum(die)
                if e is not None:
                    enums.append(e)
            elif tag in ("structure_type", "class_type"):
                r = self._normalize_record(die)
                if r is not None:
                    records.append(r)
            elif tag == "union_type":
                u = self._normalize_union(die)
                if u is not None:
                    unions.append(u)
            elif tag == "variable":
                variables.append(self._normalize_variable(die))
            elif tag == "subprogram":
                fn = self._normalize_function(die)
                if fn is not None:
                    functions.append(fn)
            # Recurse
            for ch in getattr(die, "children", []) or []:
                walk(ch)

        walk(start_die)

        decls = {
            "typedefs": typedefs,
            "enums": enums,
            "records": records,
            "unions": unions,
            "variables": variables,
            "functions": functions,
        }
        if isinstance(key, int):
            self._decls_cache[key] = decls
        return decls

    # ------------- Normalization utilities -----------------------------------
    def _name_of(self, die: model.DebugInformationEntry) -> str:
        """Extract name attribute from DIE.

        Args:
            die: Debug Information Entry

        Returns:
            Name as string, or empty string if unavailable
        """
        a = getattr(die, "attributes_map", {}).get("name") if hasattr(die, "attributes_map") else None
        if a is None:
            for x in die.attributes or []:
                if x.name == "name":
                    a = x
                    break
        if a is None or a.raw_value in (None, ""):
            return ""
        try:
            return str(a.raw_value)
        except Exception:
            return ""

    def _raw_attr(self, die: model.DebugInformationEntry, name: str, converter: type = None):
        """Get raw attribute value with optional type conversion.

        Args:
            die: Debug Information Entry
            name: Attribute name to retrieve
            converter: Optional type converter (e.g., int, str)

        Returns:
            Attribute value (optionally converted), or None if not found
        """
        amap = getattr(die, "attributes_map", None)
        if amap is not None and name in amap:
            if converter is not None:
                return converter(amap[name].raw_value)
            else:
                return amap[name].raw_value
        for a in die.attributes or []:
            if a.name == name:
                if converter is not None:
                    return converter(a.raw_value)
                else:
                    return a.raw_value
        return None

    def _render_type(self, t: Any) -> str:
        """Render a C-like type string from parsed type tree.

        Handles base types, typedefs, structs, unions, enums, pointers, arrays,
        const/volatile qualifiers, and references. Falls back to tag/name when
        structure is incomplete.

        Args:
            t: Parsed type dict from AttributeParser or CircularReference marker

        Returns:
            Type string suitable for C code (e.g., "const int *", "struct foo[10]")

        Example:
            ```python
            type_dict = ap.parse_type(offset)
            type_str = gen._render_type(type_dict)
            # "const int *" or "struct point" or "uint32_t[10]"
            ```
        """
        # Non-dict markers like CircularReference
        if not isinstance(t, dict):
            return getattr(t, "name", getattr(t, "tag", "<type>"))

        tag = t.get("tag", "<type>")
        attrs = t.get("attrs", {}) if isinstance(t.get("attrs"), dict) else {}
        name = attrs.get("name")

        # Named simple types
        if tag in ("base_type", "typedef", "unspecified_type"):
            return str(name) if name else tag

        # Records and enums
        if tag in ("structure_type", "class_type"):
            return f"struct {name}" if name else "struct <anon>"
        if tag == "union_type":
            return f"union {name}" if name else "union <anon>"
        if tag == "enumeration_type":
            return f"enum {name}" if name else "enum <anon>"

        # Type wrappers/modifiers
        if tag == "pointer_type":
            inner = attrs.get("type")
            return f"{self._render_type(inner)} *" if inner is not None else "void *"
        if tag == "reference_type":
            inner = attrs.get("type")
            return f"{self._render_type(inner)} &" if inner is not None else "<ref> &"
        if tag == "rvalue_reference_type":
            inner = attrs.get("type")
            return f"{self._render_type(inner)} &&" if inner is not None else "<ref> &&"
        if tag == "const_type":
            inner = attrs.get("type")
            return f"const {self._render_type(inner)}" if inner is not None else "const <type>"
        if tag == "volatile_type":
            inner = attrs.get("type")
            return f"volatile {self._render_type(inner)}" if inner is not None else "volatile <type>"
        if tag == "array_type":
            elem = attrs.get("type")
            elem_s = self._render_type(elem) if elem is not None else "<elem>"
            # Collect dimensions from subrange_type children using count/upper_bound-lower_bound+1
            dims: list[str] = []
            for ch in t.get("children", []) or []:
                if ch.get("tag") == "subrange_type":
                    a = ch.get("attrs") or {}
                    count = a.get("count")
                    ub = a.get("upper_bound")
                    lb = a.get("lower_bound")
                    size = None
                    try:
                        if isinstance(count, int):
                            size = int(count)
                        else:
                            ubi = int(ub) if ub is not None else None
                            lbi = int(lb) if lb is not None else 0
                            if ubi is not None:
                                size = ubi - lbi + 1
                    except Exception:
                        size = None
                    if isinstance(size, int) and size >= 0:
                        dims.append(f"[{size}]")
                    else:
                        dims.append("[]")
            if not dims:
                dims.append("[]")
            return elem_s + "".join(dims)

        # Fallback: prefer name, else tag
        return str(name) if name else tag

    def _render_head_suffix(self, t: Any) -> tuple[str, str]:
        """Render type into (head, suffix) separating array dimensions.

        For array types, returns the element type in head and dimensions in suffix.
        For non-array types, returns full type in head with empty suffix.

        Args:
            t: Parsed type dict from AttributeParser

        Returns:
            Tuple of (type_head, array_suffix)
            - type_head: Type without array dimensions (e.g., "const int *")
            - array_suffix: Array dimensions (e.g., "[10][20]")

        Example:
            ```python
            # For "int arr[10][20]"
            head, suffix = gen._render_head_suffix(type_dict)
            # head = "int", suffix = "[10][20]"
            
            # For "const char *"
            head, suffix = gen._render_head_suffix(type_dict)
            # head = "const char *", suffix = ""
            ```

        Note:
            This separation allows proper C syntax: `type_head name array_suffix;`
        """
        # Non-dict markers
        if not isinstance(t, dict):
            return (getattr(t, "name", getattr(t, "tag", "<type>")), "")

        tag = t.get("tag", "<type>")
        attrs = t.get("attrs", {}) if isinstance(t.get("attrs"), dict) else {}

        if tag == "array_type":
            # Split inner first, then add dimensions to suffix
            inner = attrs.get("type")
            head, suffix = self._render_head_suffix(inner) if inner is not None else ("<elem>", "")
            dims: list[str] = []
            for ch in t.get("children", []) or []:
                if ch.get("tag") == "subrange_type":
                    a = ch.get("attrs") or {}
                    count = a.get("count")
                    ub = a.get("upper_bound")
                    lb = a.get("lower_bound")
                    size = None
                    try:
                        if isinstance(count, int):
                            size = int(count)
                        else:
                            ubi = int(ub) if ub is not None else None
                            lbi = int(lb) if lb is not None else 0
                            if ubi is not None:
                                size = ubi - lbi + 1
                    except Exception:
                        size = None
                    if isinstance(size, int) and size >= 0:
                        dims.append(f"[{size}]")
                    else:
                        dims.append("[]")
            if not dims:
                dims.append("[]")
            return (head, suffix + "".join(dims))

        # For everything else, keep full representation in head
        return (self._render_type(t), "")

    @lru_cache(maxsize=16384)
    def _split_type_desc(self, offset: int | None) -> tuple[str, str]:
        """Resolve type at DIE offset and return (head, suffix) tuple.

        Args:
            offset: Absolute DIE offset of type, or None

        Returns:
            Tuple of (type_head, array_suffix)
            - For None offset: ("void", "")
            - For invalid offset: ("<type@0x...>", "")
            - For valid type: Type split into head and array suffix

        Note:
            Results are LRU-cached (16K entries) to avoid redundant parsing.
        """
        if isinstance(offset, int):
            try:
                t = self.ap.parse_type(offset)
            except Exception:
                t = None
            if t is None:
                return (f"<type@0x{offset:08x}>", "")
            return self._render_head_suffix(t)
        return ("void", "")

    def _type_desc(self, offset: int | None) -> str:
        """Get complete type description as single string.

        Args:
            offset: Absolute DIE offset of type, or None

        Returns:
            Complete type string (head + suffix concatenated)

        Note:
            This is a convenience wrapper over _split_type_desc for cases
            where array suffix separation is not needed.
        """
        # Backward-compatible single string (used in some places). Prefer split version for declarations.
        head, suffix = self._split_type_desc(offset)
        return head + suffix

    def _collect_members(self, die: model.DebugInformationEntry) -> list[dict[str, Any]]:
        """Collect and normalize struct/union/class members.

        Extracts all member DIEs and handles:
            - Named members with explicit types
            - Anonymous inline struct/union/enum definitions
            - Member offsets (data_member_location)

        Args:
            die: Structure, class, or union DIE

        Returns:
            List of member dicts, each containing:
                - name: Member name (or "<anon>")
                - type: Full type string (if not inline)
                - type_head: Type without array suffix
                - type_suffix: Array dimensions
                - inline: True if anonymous inline type
                - inline_kind: "struct", "union", or "enum" (if inline)
                - inline_members: Nested members (if inline struct/union)
                - inline_items: Enumerator list (if inline enum)
                - location: Member offset expression

        Example:
            ```python
            struct_die = session.query(DebugInformationEntry).filter_by(
                tag="structure_type", name="my_struct"
            ).first()
            members = gen._collect_members(struct_die)
            for m in members:
                if m.get('inline'):
                    print(f"Anonymous {m['inline_kind']}: {m['name']}")
                else:
                    print(f"{m['type']} {m['name']}{m.get('type_suffix', '')}")
            ```
        """
        members: list[dict[str, Any]] = []
        for ch in getattr(die, "children", []) or []:
            ctag = getattr(ch.abbrev, "tag", ch.tag)
            if ctag == "member":
                name = self._name_of(ch)
                toff = self._raw_attr(ch, "type", int)
                mloc = self._raw_attr(ch, "data_member_location")
                # Inline anonymous compound types (struct/union/enum)
                if isinstance(toff, int):
                    type_die = self.ap.get_die(int(toff))
                    if type_die is not None:
                        ttag = getattr(type_die.abbrev, "tag", type_die.tag)
                        tname = self._name_of(type_die)
                        if (not tname) and ttag in ("structure_type", "class_type", "union_type", "enumeration_type"):
                            # Build inline definition
                            if ttag in ("structure_type", "class_type", "union_type"):
                                inline_kind = "struct" if ttag in ("structure_type", "class_type") else "union"
                                inner_members: list[dict[str, Any]] = []
                                for mm in getattr(type_die, "children", []) or []:
                                    if getattr(mm.abbrev, "tag", mm.tag) == "member":
                                        mm_name = self._name_of(mm) or "<anon>"
                                        mm_to = self._raw_attr(mm, "type", int)
                                        if isinstance(mm_to, int):
                                            mm_head, mm_suf = self._split_type_desc(int(mm_to))
                                            mm_tstr = mm_head + mm_suf
                                        else:
                                            mm_head, mm_suf, mm_tstr = "<unknown>", "", "<unknown>"
                                        inner_members.append(
                                            {
                                                "name": mm_name,
                                                "type": mm_tstr,
                                                "type_head": mm_head,
                                                "type_suffix": mm_suf,
                                            }
                                        )
                                members.append(
                                    {
                                        "name": name or "<anon>",
                                        "inline": True,
                                        "inline_kind": inline_kind,
                                        "inline_members": inner_members,
                                        "location": mloc,
                                    }
                                )
                                continue
                            elif ttag == "enumeration_type":
                                items: list[tuple[str, Any]] = []
                                for en in getattr(type_die, "children", []) or []:
                                    if getattr(en.abbrev, "tag", en.tag) == "enumerator":
                                        en_name = self._name_of(en) or "<anon>"
                                        en_val = self._raw_attr(en, "const_value")
                                        items.append((en_name, en_val))
                                members.append(
                                    {
                                        "name": name or "<anon>",
                                        "inline": True,
                                        "inline_kind": "enum",
                                        "inline_items": items,
                                        "location": mloc,
                                    }
                                )
                                continue
                    # Not an anonymous compound: render as normal type
                    head, suffix = self._split_type_desc(int(toff))
                    tstr = head + suffix
                else:
                    head, suffix = ("<unknown>", "")
                    tstr = "<unknown>"
                members.append(
                    {
                        "name": name or "<anon>",
                        "type": tstr,
                        "type_head": head,
                        "type_suffix": suffix,
                        "location": mloc,
                    }
                )
        return members

    def _normalize_typedef(self, die: model.DebugInformationEntry) -> dict[str, Any]:
        """Normalize typedef DIE into template-ready dict.

        Args:
            die: Typedef DIE

        Returns:
            Dict with keys: name, target, target_head, target_suffix
        """
        name = self._name_of(die) or "<anon_typedef>"
        toff = self._raw_attr(die, "type", int)
        if isinstance(toff, int):
            head, suffix = self._split_type_desc(int(toff))
            target = head + suffix
        else:
            head, suffix, target = "<unknown>", "", "<unknown>"
        return {"name": name, "target": target, "target_head": head, "target_suffix": suffix}

    def _normalize_enum(self, die: model.DebugInformationEntry) -> dict[str, Any] | None:
        """Normalize enumeration DIE into template-ready dict.

        Args:
            die: Enumeration_type DIE

        Returns:
            Dict with keys: name, items [(name, value), ...], byte_size
            Returns None for anonymous enums (skipped at top level)
        """
        name_raw = self._name_of(die)
        if not name_raw:
            return None  # Skip anonymous enums as standalone entities
        name = name_raw
        items: list[tuple[str, Any]] = []
        for ch in getattr(die, "children", []) or []:
            if getattr(ch.abbrev, "tag", ch.tag) == "enumerator":
                nm = self._name_of(ch) or "<anon>"
                val = self._raw_attr(ch, "const_value")
                items.append((nm, val))
        bsize = self._raw_attr(die, "byte_size", int)
        return {"name": name, "items": items, "byte_size": bsize}

    def _normalize_record(self, die: model.DebugInformationEntry) -> dict[str, Any] | None:
        """Normalize structure/class DIE into template-ready dict.

        Args:
            die: Structure_type or class_type DIE

        Returns:
            Dict with keys: kind ("struct"), name, members, byte_size
            Returns None for anonymous structs (skipped at top level)
        """
        name_raw = self._name_of(die)
        if not name_raw:
            return None  # Skip anonymous structs/classes as standalone entities
        name = name_raw
        members = self._collect_members(die)
        size = self._raw_attr(die, "byte_size", int)
        return {"kind": "struct", "name": name, "members": members, "byte_size": size}

    def _normalize_union(self, die: model.DebugInformationEntry) -> dict[str, Any] | None:
        """Normalize union DIE into template-ready dict.

        Args:
            die: Union_type DIE

        Returns:
            Dict with keys: kind ("union"), name, members, byte_size
            Returns None for anonymous unions (skipped at top level)
        """
        name_raw = self._name_of(die)
        if not name_raw:
            return None  # Skip anonymous unions as standalone entities
        name = name_raw
        members = self._collect_members(die)
        size = self._raw_attr(die, "byte_size", int)
        return {"kind": "union", "name": name, "members": members, "byte_size": size}

    def _normalize_variable(self, die: model.DebugInformationEntry) -> dict[str, Any]:
        """Normalize variable DIE into template-ready dict.

        Args:
            die: Variable DIE

        Returns:
            Dict with keys: name, type, type_head, type_suffix, location
        """
        name = self._name_of(die) or "<anon>"
        toff = self._raw_attr(die, "type", int)
        loc = self._raw_attr(die, "location")
        if isinstance(toff, int):
            head, suffix = self._split_type_desc(int(toff))
            tstr = head + suffix
        else:
            head, suffix, tstr = "<unknown>", "", "<unknown>"
        return {
            "name": name,
            "type": tstr,
            "type_head": head,
            "type_suffix": suffix,
            "location": loc,
        }

    def _normalize_function(self, die: model.DebugInformationEntry) -> dict[str, Any] | None:
        """Normalize subprogram DIE into template-ready function prototype dict.

        Args:
            die: Subprogram DIE

        Returns:
            Dict with keys: name, returns, returns_head, returns_suffix, params
            Returns None for unnamed subprograms (skipped)
        """
        name = self._name_of(die)
        if not name:
            # Skip unnamed subprograms for prototypes
            return None
        rtoff = self._raw_attr(die, "type", int)
        rthead, rtsuf = self._split_type_desc(int(rtoff)) if isinstance(rtoff, int) else ("void", "")
        returns = rthead + rtsuf
        params: list[dict[str, Any]] = []
        for ch in getattr(die, "children", []) or []:
            if getattr(ch.abbrev, "tag", ch.tag) == "formal_parameter":
                pname = self._name_of(ch) or "param"
                ptoff = self._raw_attr(ch, "type", int)
                if isinstance(ptoff, int):
                    phead, psuf = self._split_type_desc(int(ptoff))
                    ptype = phead + psuf
                else:
                    phead, psuf, ptype = "<unknown>", "", "<unknown>"
                params.append(
                    {
                        "name": pname,
                        "type": ptype,
                        "type_head": phead,
                        "type_suffix": psuf,
                    }
                )
        return {"name": name, "returns": returns, "returns_head": rthead, "returns_suffix": rtsuf, "params": params}

    # ------------- Rendering --------------------------------------------------
    def _render_header(self, decls: dict[str, list[dict[str, Any]]], guard: str | None) -> str:
        """Render normalized declarations into complete C header file.

        Args:
            decls: Dict of declaration lists from generate_declarations()
            guard: Include guard macro name, or None to skip guards

        Returns:
            Complete C header file as string
        """
        tmpl = Template(self._HEADER_TEMPLATE)
        return tmpl.render(
            guard=guard,
            typedefs=decls.get("typedefs", []),
            enums=decls.get("enums", []),
            records=decls.get("records", []),
            unions=decls.get("unions", []),
            variables=decls.get("variables", []),
            functions=decls.get("functions", []),
            opt=self.options,
        )

    def _guard_name(self, header_name: str | None) -> str:
        """Generate include guard macro name from header filename.

        Args:
            header_name: Optional header filename (e.g., "my_types.h")

        Returns:
            Include guard macro (e.g., "_MY_TYPES_H_")

        Note:
            Uses self.options.header_guard if set, otherwise auto-generates
            from filename by uppercasing and replacing non-alphanumeric chars with "_".
        """
        if self.options.header_guard:
            return self.options.header_guard
        base = header_name or "GENERATED_DWARF_HEADER"
        base = base.upper()
        sanitized = []
        for ch in base:
            if ch.isalnum():
                sanitized.append(ch)
            else:
                sanitized.append("_")
        return "_" + "".join(sanitized) + "_"

    # ------------- Templates --------------------------------------------------
    _HEADER_TEMPLATE = r"""
% if guard:
#ifndef ${guard}
#define ${guard}
% endif

/* Generated by objutils.dwarf.c_generator using DWARF DIEs */

% if typedefs:
/* Typedefs */
% for t in typedefs:
typedef ${t.get('target_head', t['target'])} ${t['name']}${t.get('target_suffix','')};
% endfor

% endif
% if enums:
/* Enums */
% for e in enums:
typedef enum ${e['name']} {
% for (n, v) in e['items']:
    ${n}${(' = ' + (('-0x%x' % abs(int(v))) if int(v) < 0 else ('0x%x' % int(v)))) if v is not None else ''},
% endfor
} ${e['name']};
% endfor

% endif
% if records:
/* Structs / Classes */
% for r in records:
typedef struct ${r['name']} {
% for m in r['members']:
% if m.get('inline'):
% if m.get('inline_kind') in ('struct','union'):
    ${m['inline_kind']} {
% for mm in m.get('inline_members', []) or []:
        ${mm.get('type_head', mm['type'])} ${mm['name']}${mm.get('type_suffix','')};
% endfor
    } ${m['name']};
% elif m.get('inline_kind') == 'enum':
    enum {
% for (n, v) in m.get('inline_items', []) or []:
        ${n}${(' = ' + (('-0x%x' % abs(int(v))) if (v is not None and int(v) < 0) else ('0x%x' % int(v)))) if v is not None else ''},
% endfor
    } ${m['name']};
% else:
    ${m.get('type_head', m['type'])} ${m['name']}${m.get('type_suffix','')};
% endif
% else:
    ${m.get('type_head', m['type'])} ${m['name']}${m.get('type_suffix','')};
% endif
% endfor
} ${r['name']};
% endfor

% endif
% if unions:
/* Unions */
% for u in unions:
typedef union ${u['name']} {
% for m in u['members']:
% if m.get('inline'):
% if m.get('inline_kind') in ('struct','union'):
    ${m['inline_kind']} {
% for mm in m.get('inline_members', []) or []:
        ${mm.get('type_head', mm['type'])} ${mm['name']}${mm.get('type_suffix','')};
% endfor
    } ${m['name']};
% elif m.get('inline_kind') == 'enum':
    enum {
% for (n, v) in m.get('inline_items', []) or []:
        ${n}${(' = ' + (('-0x%x' % abs(int(v))) if (v is not None and int(v) < 0) else ('0x%x' % int(v)))) if v is not None else ''},
% endfor
    } ${m['name']};
% else:
    ${m.get('type_head', m['type'])} ${m['name']}${m.get('type_suffix','')};
% endif
% else:
    ${m.get('type_head', m['type'])} ${m['name']}${m.get('type_suffix','')};
% endif
% endfor
} ${u['name']};
% endfor

% endif
% if variables:
/* Extern variables (declarations) */
% for v in variables:
extern ${v.get('type_head', v['type'])} ${v['name']}${v.get('type_suffix','')};
% endfor

% endif
% if functions:
/* Function prototypes */
% for f in functions:
${f['returns']} ${f['name']}(${', '.join([p.get('type_head', p['type']) + ' ' + p['name'] + p.get('type_suffix','') for p in f['params']]) if f['params'] else 'void'});
% endfor
% endif

% if guard:
#endif /* ${guard} */
% endif
"""
    """str: Mako template for C header file generation.

    Template Variables:
        guard: Include guard macro name (or None)
        typedefs: List of typedef dicts
        enums: List of enum dicts with 'items' [(name, value), ...]
        records: List of struct/class dicts with 'members'
        unions: List of union dicts with 'members'
        variables: List of variable dicts for extern declarations
        functions: List of function prototype dicts with 'params'
        opt: RenderOptions instance

    Generated Structure:
        1. Include guard (if enabled)
        2. Generator comment
        3. Typedefs section
        4. Enums section (with hex values)
        5. Structs/Classes section (with inline anonymous types)
        6. Unions section (with inline anonymous types)
        7. Extern variable declarations
        8. Function prototypes
        9. Include guard end

    Note:
        Anonymous inline types (struct/union/enum) are rendered inline within
        their containing struct/union definition.
    """
