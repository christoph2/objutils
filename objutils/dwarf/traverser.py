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


def is_type_encoding(encoding: Union[int, AttributeEncoding]) -> bool:
    return encoding in DWARF_TYPE_ENCODINGS


@dataclass
class CompiledUnit:
    name: str
    comp_dir: str
    producer: str
    language: str


@dataclass
class DIE:
    tag: str
    children: list[Any] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Variable:
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


# 'data_member_location': b'#\x00',


def get_attribute(attrs: dict[str, DIEAttribute], key: str, default: Union[int, str]) -> Union[int, str]:
    attr: Optional[DIEAttribute] = attrs.get(key)
    if attr is None:
        return default
    else:
        return attr.raw_value


class CompiledUnitsSummary:

    def __init__(self, session) -> None:
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
    cus = session.query(model.DebugInformationEntry).filter(model.DebugInformationEntry.tag == Tag.compile_unit).all()
    for idx, cu in enumerate(cus):
        name = cu.attributes_map.get("name", "N/A").raw_value
        producer = cu.attributes_map.get("producer", "N/A").raw_value
        comp_dir = cu.attributes_map.get("comp_dir", "N/A").raw_value
        language = cu.attributes_map.get("language", "N/A").raw_value
        print(f"Compile Unit #{idx}: {name!r}, Name: {comp_dir!r} Producer: {producer!r}, Language: {language!r}")


@dataclass
class CircularReference:
    tag: str
    name: str


class AttributeParser:
    """
    Parse and traverse DIE trees and their type relationships with caching.

    Caching strategy (only here):
    - parsed_types: memoizes fully parsed type dicts by DIE offset
    - get_die(): LRU-cached DB lookup by offset to minimize ORM traffic
    - attributes_map: leverages the ORM-side per-instance cache (if present)
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
        """
        Create an AttributeParser.

        Parameters
        ----------
        session_or_path:
            Either an existing SQLAlchemy session (backward compatible) or a path to an ELF/.prgdb file.
            If a path is given, the corresponding program database will be opened (and imported if needed).
        import_if_needed: bool
            When a path to an ELF is provided, import DWARF into a sibling .prgdb if it doesn't exist yet.
        force_import: bool
            Force re-import when creating the database from an ELF path.
        quiet: bool
            Suppress non-error output during on-demand import when a path is provided.
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
        address_size = elf_header.address_size
        endianess = Endianess.Little if elf_header.endianess == defs.ELFDataEncoding.ELFDATA2LSB else Endianess.Big
        factory = DwarfReaders(
            endianess=endianess,
            address_size=address_size,
            strings=debug_str,
            line_strings=debug_line_str,
        )
        # BaseTypeEncoding
        self.endianess = endianess
        self.is_64bit = elf_header.is_64bit
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
        """Return a fully traversed type tree as a dict.

        Accepts one of:
        - a DIE offset (absolute),
        - a DIE instance that has a DW_AT_type attribute,
        - a DIEAttribute instance (DW_AT_type) whose value references a type.

        The returned dictionary contains:
        - tag: DWARF tag name for the type DIE
        - attrs: non-structural attributes with values; nested "type" attributes
                 are resolved recursively into dicts
        - children: list of child DIE dicts (e.g., members, enumerators, subranges)

        Circular references are represented by CircularReference(tag, name).
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
        """Resolve a DW_AT_type attribute's value to an absolute DIE offset.

        Handles CU-relative reference forms by adding the DIE's cu_start.
        Returns None if the attribute cannot be interpreted as an integer offset.
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
        return self.session.query(model.DebugInformationEntry).filter_by(offset=offset).one_or_none()

    def traverse_tree(self, entry: model.DebugInformationEntry, level: int = 0) -> None:
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
        if hasattr(die, "attributes_map"):
            return die.attributes_map.get(name)
        for a in die.attributes or []:
            if a.name == name:
                return a
        return None

    def _attr_raw(self, die: model.DebugInformationEntry, name: str):
        a = self._get_attr(die, name)
        return None if a is None else a.raw_value

    def _name_of(self, die: model.DebugInformationEntry) -> str:
        try:
            return self._attr_raw(die, "name") or ""
        except Exception:
            return ""

    def _type_summary(self, offset: int) -> str:
        die = self.get_die(offset)
        if die is None:
            return f"<missing type at 0x{offset:08x}>"
        tag = getattr(die.abbrev, "tag", die.tag)
        name = self._name_of(die)
        return name or tag
