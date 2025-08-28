"""
C/C++ Code Generator from DWARF DIEs using Mako templates.

This module builds on top of AttributeParser to reconstruct enough structure
information to render C/C++ declarations for:
- typedefs
- enums
- structs/classes/unions (with members and inheritance where available)
- variables
- function prototypes (subprogram/formal_parameter)

Design goals
- Keep logic and caching local to this module (and AttributeParser).
- Avoid modifying core parsers or DB schema.
- Use simple inline Mako templates to minimize repository churn.

Usage (example):
    from objutils.elf import ElfParser
    from objutils.dwarf import DwarfProcessor
    from objutils.dwarf.c_generator import CGenerator

    ep = ElfParser("file.elf")
    dp = DwarfProcessor(ep)
    dp.do_dbg_info()

    session = ep.session
    start_die = session.query(model.DebugInformationEntry).first()
    gen = CGenerator(session)
    code = gen.generate_header(start_die)
    print(code)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from mako.template import Template

from objutils.dwarf.attrparser import AttributeParser
from objutils.elf import model


@dataclass
class RenderOptions:
    language: str = "c"  # or "c++" (reserved for future)
    indent: str = "    "
    include_guards: bool = True
    header_guard: str | None = None


class CGenerator:
    def __init__(self, session, attribute_parser: AttributeParser | None = None, options: RenderOptions | None = None):
        self.session = session
        self.ap = attribute_parser or AttributeParser(session)
        self.options = options or RenderOptions()

    # ------------- Public API -------------------------------------------------
    def generate_header(self, start_die: model.DebugInformationEntry, header_name: str | None = None) -> str:
        decls = self.generate_declarations(start_die)
        hdr_guard = self._guard_name(header_name) if self.options.include_guards else None
        return self._render_header(decls, hdr_guard)

    def generate_declarations(self, start_die: model.DebugInformationEntry) -> dict[str, list[dict[str, Any]]]:
        """Traverse DIE subtree and collect declarations grouped by category.
        Returns a dict with keys: typedefs, enums, records, unions, variables, functions.
        Each value is a list of normalized dicts ready for templating.
        """
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

        return {
            "typedefs": typedefs,
            "enums": enums,
            "records": records,
            "unions": unions,
            "variables": variables,
            "functions": functions,
        }

    # ------------- Normalization utilities -----------------------------------
    def _name_of(self, die: model.DebugInformationEntry) -> str:
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
        """Render a C-like type string from a parsed type dict (from AttributeParser).
        Supports base/typedef/struct/union/enum, pointer/array, const/volatile, and references.
        Falls back to tag/name when structure is incomplete.
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
        """Render type into (head, suffix) separating array dimensions into suffix.
        For non-array types, suffix is empty and head equals _render_type(t).
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

    def _split_type_desc(self, offset: int | None) -> tuple[str, str]:
        """Return (head, suffix) for a type at DIE offset.
        head is the type specifier with pointer/ref/qualifiers, suffix carries array dimensions like [3][N].
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
        # Backward-compatible single string (used in some places). Prefer split version for declarations.
        head, suffix = self._split_type_desc(offset)
        return head + suffix

    def _collect_members(self, die: model.DebugInformationEntry) -> list[dict[str, Any]]:
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
        name = self._name_of(die) or "<anon_typedef>"
        toff = self._raw_attr(die, "type", int)
        if isinstance(toff, int):
            head, suffix = self._split_type_desc(int(toff))
            target = head + suffix
        else:
            head, suffix, target = "<unknown>", "", "<unknown>"
        return {"name": name, "target": target, "target_head": head, "target_suffix": suffix}

    def _normalize_enum(self, die: model.DebugInformationEntry) -> dict[str, Any] | None:
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
        name_raw = self._name_of(die)
        if not name_raw:
            return None  # Skip anonymous structs/classes as standalone entities
        name = name_raw
        members = self._collect_members(die)
        size = self._raw_attr(die, "byte_size", int)
        return {"kind": "struct", "name": name, "members": members, "byte_size": size}

    def _normalize_union(self, die: model.DebugInformationEntry) -> dict[str, Any] | None:
        name_raw = self._name_of(die)
        if not name_raw:
            return None  # Skip anonymous unions as standalone entities
        name = name_raw
        members = self._collect_members(die)
        size = self._raw_attr(die, "byte_size", int)
        return {"kind": "union", "name": name, "members": members, "byte_size": size}

    def _normalize_variable(self, die: model.DebugInformationEntry) -> dict[str, Any]:
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
