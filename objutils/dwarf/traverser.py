from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import groupby
from typing import Any, Dict, Optional, Union

from objutils.dwarf.constants import AttributeEncoding, Tag
from objutils.elf import model
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


def get_attribute(attrs: dict[str, DIEAttribute], key: str, default: Union[int, str]) -> Union[int, str]:
    attr: Optional[DIEAttribute] = attrs.get(key)
    if attr is None:
        return default
    else:
        return attr.display_value


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
        name = cu.attributes_map.get("name", "N/A").display_value
        producer = cu.attributes_map.get("producer", "N/A").display_value
        comp_dir = cu.attributes_map.get("comp_dir", "N/A").display_value
        language = cu.attributes_map.get("language", "N/A").display_value
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

    def __init__(self, session):
        self.session = session
        self.type_stack: set[int] = set()
        self.parsed_types: dict = {}
        self.att_types: dict = defaultdict(set)

    # The cache lives per-instance because "self" participates in the key.
    @lru_cache(maxsize=8192)
    def get_die(self, offset: int) -> model.DebugInformationEntry | None:
        return self.session.query(model.DebugInformationEntry).filter_by(offset=offset).one_or_none()

    def traverse_tree(self, entry: model.DebugInformationEntry, level: int = 0) -> None:
        tag = getattr(entry.abbrev, "tag", entry.tag)
        name = self._name_of(entry)
        type_info = ""
        if "type" in getattr(entry, "attributes_map", {}):
            type_offset = self._attr_raw(entry, "type")
            if type_offset is not None:
                type_info = f" -> {self._type_summary(int(type_offset))}"

        print(f"{'    ' * level}{tag} '{name}'{type_info} [off=0x{entry.offset:08x}]")

        for child in getattr(entry, "children", []) or []:
            self.traverse_tree(child, level + 1)

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
                if referenced_offset and referenced_offset != die.offset:
                    result.setdefault("attrs", {})[attr_name] = self.parse_type(referenced_offset, level + 1)
                    continue

            # Default: keep raw_value to stay close to DB content
            result.setdefault("attrs", {})[attr_name] = attr.raw_value

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
            return f"<missing type at {offset}>"
        tag = getattr(die.abbrev, "tag", die.tag)
        name = self._name_of(die)
        return name or tag
