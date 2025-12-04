from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import groupby
from typing import Any, Optional, Union

from objutils.dwarf.constants import (
    Accessibility,
    AttributeEncoding,
    AttributeForm,
    BaseTypeEncoding,
    CallingConvention,
    Defaulted,
    DecimalSign,
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

}


def get_attribute(attrs: dict[str, DIEAttribute], key: str, default: Union[int, str]) -> Union[int, str]:
    attr: Optional[DIEAttribute] = attrs.get(key)
    if attr is None:
        return default
    else:
        return attr.raw_value


class CompiledUnitsSummary:

    def __init__(self, session) -> None:
        cus = session.query(model.DebugInformationEntry).filter(
            model.DebugInformationEntry.tag == Tag.compile_unit).all()
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
                        tp = session.query(model.DebugInformationEntry).filter(
                            model.DebugInformationEntry.offset == tpx).first()
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

    # class Endianess(IntEnum):
    #    Little = 0
    #    Big = 1

    def __init__(self, session_or_path, *, import_if_needed: bool = True, force_import: bool = False,
                 quiet: bool = True):
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
        self.readers = factory.readers
        self.stack_machine = factory.stack_machine
        self.dwarf_expression = factory.dwarf_expression

    @lru_cache(maxsize=64 * 1024)
    def type_tree(self, obj: Union[int, model.DebugInformationEntry, DIEAttribute]) -> dict[
                                                                                           str, Any] | CircularReference:
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
            return self.parse_type(off)

        # Fallback
        return {"tag": "<unsupported>", "attrs": {}}

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
            location = self.dwarf_expression(entry.attributes_map["location"].form,
                                             entry.attributes_map["location"].raw_value)
            print(f"{'    ' * level}{tag} '{name}'{type_info} [location={location}] [off=0x{entry.offset:08x}]")
        else:
            if tag == "enumerator" and "const_value" in entry.attributes_map:
                enumerator_value = int(entry.attributes_map["const_value"].raw_value)
                print(
                    f"{'    ' * level}{tag} '{name}'{type_info} [value=0x{enumerator_value:04x}] [off=0x{entry.offset:08x}]")
            elif tag == 'subrange_type':
                lower_bound = 0
                upper_bound = 0
                if "lower_bound" in entry.attributes_map:
                    lower_bound = int(entry.attributes_map["lower_bound"].raw_value)
                if "upper_bound" in entry.attributes_map:
                    upper_bound = int(entry.attributes_map["upper_bound"].raw_value)
                print(
                    f"{'    ' * level}{tag} '{name}'{type_info} [lower_bound={lower_bound}: upper_bound={upper_bound}] [off=0x{entry.offset:08x}]")
            elif tag == "member" and "data_member_location" in entry.attributes_map:
                data_member_location = self.dwarf_expression(
                    entry.attributes_map["data_member_location"].form,
                    entry.attributes_map["data_member_location"].raw_value
                )
                print(
                    f"{'    ' * level}{tag} '{name}'{type_info} [location={data_member_location}] [off=0x{entry.offset:08x}]")
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
