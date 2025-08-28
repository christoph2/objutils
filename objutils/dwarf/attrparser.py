"""
AttributeParser: DWARF DIE attribute/type traversal with localized caching.

This module provides a complete and optimized version of the AttributeParser that
was previously drafted in a scratch script. Caching is implemented ONLY here, as
requested:

- Per-instance memoization of parsed types (parsed_types)
- LRU cache for DIE lookups by CU-relative offset (get_die)
- Cycle detection via type_stack to prevent infinite recursion

Usage example (pseudo):

    from objutils.elf import ElfParser
    from objutils.dwarf import DwarfProcessor
    from objutils.dwarf.attrparser import AttributeParser, traverse_dict

    ep = ElfParser(<elf-path>)
    dp = DwarfProcessor(ep)
    dp.do_dbg_info()

    session = ep.session
    root = session.query(model.DebugInformationEntry).first()
    ap = AttributeParser(session)
    ap.traverse_tree(root)

Notes:
- The parser expects the ORM schema with DebugInformationEntry including
  attributes, children, parent, offset and the convenience attributes_map.
- Type references are assumed to be encoded as DIE offsets (CU-relative) stored
  in DIEAttribute.raw_value for the "type" attribute and similar.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Set, Union

from objutils.elf import model


def lev_print(level: int, *args: Any, **kws: Any) -> None:
    print("    " * level, *args, **kws)


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
        "decl_file",
        "decl_line",
        "decl_column",
        "sibling",
    }

    def __init__(self, session):
        self.session = session
        # Used to detect cycles while descending type links
        self.type_stack: set[int] = set()
        # Parsed type cache: offset -> structured dict
        self.parsed_types: dict[int, dict[str, Any]] = {}
        # Tag -> set(attributes encountered) for insights/statistics
        self.att_types: dict[str, set[str]] = defaultdict(set)

    # LRU cache on a helper method to lookup DIEs by offset.
    # The cache lives per-instance because "self" participates in the key.
    @lru_cache(maxsize=8192)
    def get_die(self, offset: int) -> model.DebugInformationEntry | None:
        return self.session.query(model.DebugInformationEntry).filter(model.DebugInformationEntry.offset == offset).first()

    # --- Helpers for summaries -------------------------------------------------
    def _get_attr(self, die: model.DebugInformationEntry, name: str):
        amap = getattr(die, "attributes_map", None)
        if amap is not None:
            return amap.get(name)
        for a in die.attributes or []:
            if a.name == name:
                return a
        return None

    def _attr_raw(self, die: model.DebugInformationEntry, name: str):
        a = self._get_attr(die, name)
        return None if a is None else a.raw_value

    def _name_of(self, die: model.DebugInformationEntry) -> str:
        a = self._get_attr(die, "name")
        try:
            return str(a.raw_value) if a is not None and a.raw_value is not None else ""
        except Exception:
            return ""

    def _type_summary(self, offset: int) -> str:
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
        """Depth-first traversal printing a summary and parsing types on-demand."""
        tag = entry.abbrev.tag if hasattr(entry, "abbrev") else entry.tag
        lev_print(level, f"Tag: {tag}")

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
            lev_print(level + 1, f"Attribute: {attr.name} = {attr.display_value}")

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


def traverse_dict(elem: dict[str, Any], level: int = 0) -> None:
    """Pretty-print a parsed type dict (recursive)."""
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
