from objutils.dwarf.c_generator import CGenerator
from objutils.elf import model as elf_model


# Helpers to construct a tiny DWARF-like tree in the ORM


def add_die(session, tag: str, offset: int, parent=None):
    die = elf_model.DebugInformationEntry(tag=tag, offset=offset)
    if parent is not None:
        die.parent = parent
    session.add(die)
    session.flush()
    return die


def add_attr(session, die, name: str, raw_value, display_value=None):
    if display_value is None:
        display_value = raw_value
    a = elf_model.DIEAttribute(name=name, raw_value=raw_value, display_value=str(display_value), entry=die)
    session.add(a)
    # invalidate attributes_map cache if present
    if hasattr(die, "_attributes_map_cache"):
        try:
            delattr(die, "_attributes_map_cache")
        except Exception:
            pass
    return a


def build_sample_db(filename: str | None = None):
    db = elf_model.Model(":memory:" if filename is None else filename)
    s = db.session

    # Base type: int
    bt_int = add_die(s, "base_type", 0x100)
    add_attr(s, bt_int, "name", "int")

    # Typedef: MyInt -> int
    td = add_die(s, "typedef", 0x110)
    add_attr(s, td, "name", "MyInt")
    add_attr(s, td, "type", bt_int.offset)

    # Enum: Color { RED=0, GREEN=1 }
    en = add_die(s, "enumeration_type", 0x120)
    add_attr(s, en, "name", "Color")
    en_red = add_die(s, "enumerator", 0x121, parent=en)
    add_attr(s, en_red, "name", "RED")
    add_attr(s, en_red, "const_value", 0)
    en_green = add_die(s, "enumerator", 0x122, parent=en)
    add_attr(s, en_green, "name", "GREEN")
    add_attr(s, en_green, "const_value", 1)

    # Struct: Point { int x; }
    st = add_die(s, "structure_type", 0x130)
    add_attr(s, st, "name", "Point")
    mem_x = add_die(s, "member", 0x131, parent=st)
    add_attr(s, mem_x, "name", "x")
    add_attr(s, mem_x, "type", bt_int.offset)

    # Variable: gVar : int
    var = add_die(s, "variable", 0x140)
    add_attr(s, var, "name", "gVar")
    add_attr(s, var, "type", bt_int.offset)

    # Subprogram: int foo(int a)
    sp = add_die(s, "subprogram", 0x150)
    add_attr(s, sp, "name", "foo")
    add_attr(s, sp, "type", bt_int.offset)  # return type
    fp_a = add_die(s, "formal_parameter", 0x151, parent=sp)
    add_attr(s, fp_a, "name", "a")
    add_attr(s, fp_a, "type", bt_int.offset)

    # Top compile unit DIE to serve as root
    cu = add_die(s, "compile_unit", 0x10)
    # attach interesting top-level DIEs as children of CU
    for child in (td, en, st, var, sp):
        child.parent = cu
    s.flush()
    s.commit()

    return db, cu


def test_cgenerator_generate_declarations_simple():
    db, cu = build_sample_db()
    try:
        gen = CGenerator(db.session)
        decls = gen.generate_declarations(cu)
        assert isinstance(decls, dict)
        assert len(decls.get("typedefs", [])) == 1
        assert len(decls.get("enums", [])) == 1
        assert len(decls.get("records", [])) == 1
        assert len(decls.get("variables", [])) == 1
        assert len(decls.get("functions", [])) == 1

        td = decls["typedefs"][0]
        assert td["name"] == "MyInt"
        assert td["target"] in ("int", "base_type")  # name preferred

        en = decls["enums"][0]
        assert en["name"] == "Color"
        names = [n for (n, v) in en["items"]]
        assert names == ["RED", "GREEN"]

        rec = decls["records"][0]
        assert rec["name"] == "Point"
        assert any(m["name"] == "x" and m["type"] in ("int", "base_type") for m in rec["members"])  # type name preferred

        var = decls["variables"][0]
        assert var["name"] == "gVar"
        assert var["type"] in ("int", "base_type")

        fn = decls["functions"][0]
        assert fn["name"] == "foo"
        assert fn["returns"] in ("int", "base_type")
        assert len(fn["params"]) == 1 and fn["params"][0]["name"] == "a"
    finally:
        db.close()


def test_cgenerator_generate_header_contains_expected_decls(tmp_path):
    db, cu = build_sample_db()
    try:
        gen = CGenerator(db.session)
        header = gen.generate_header(cu, header_name="demo.h")
        # Validate key lines
        assert "#ifndef _DEMO_H_" in header or "#ifndef _DEMO_H" in header
        assert "typedef int MyInt;" in header or "typedef base_type MyInt;" in header
        assert "typedef enum Color" in header
        assert "RED = 0x0" in header and "GREEN = 0x1" in header
        assert "typedef struct Point" in header
        # member declaration line
        assert ("int x;" in header) or ("base_type x;" in header)
        # extern var
        assert ("extern int gVar;" in header) or ("extern base_type gVar;" in header)
        # function prototype
        assert ("int foo(int a);" in header) or ("base_type foo(base_type a);" in header)
    finally:
        db.close()





# Helpers to construct a tiny DWARF-like tree in the ORM


def add_die(session, tag: str, offset: int, parent=None):
    die = elf_model.DebugInformationEntry(tag=tag, offset=offset)
    if parent is not None:
        die.parent = parent
    session.add(die)
    session.flush()
    return die


def add_attr(session, die, name: str, raw_value, display_value=None):
    if display_value is None:
        display_value = raw_value
    a = elf_model.DIEAttribute(name=name, raw_value=raw_value, display_value=str(display_value), entry=die)
    session.add(a)
    # invalidate attributes_map cache if present
    if hasattr(die, "_attributes_map_cache"):
        try:
            delattr(die, "_attributes_map_cache")
        except Exception:
            pass
    return a


def build_sample_db(filename: str | None = None):
    db = elf_model.Model(":memory:" if filename is None else filename)
    s = db.session

    # Base type: int
    bt_int = add_die(s, "base_type", 0x100)
    add_attr(s, bt_int, "name", "int")

    # Typedef: MyInt -> int
    td = add_die(s, "typedef", 0x110)
    add_attr(s, td, "name", "MyInt")
    add_attr(s, td, "type", bt_int.offset)

    # Enum: Color { RED=0, GREEN=1 }
    en = add_die(s, "enumeration_type", 0x120)
    add_attr(s, en, "name", "Color")
    en_red = add_die(s, "enumerator", 0x121, parent=en)
    add_attr(s, en_red, "name", "RED")
    add_attr(s, en_red, "const_value", 0)
    en_green = add_die(s, "enumerator", 0x122, parent=en)
    add_attr(s, en_green, "name", "GREEN")
    add_attr(s, en_green, "const_value", 1)

    # Struct: Point { int x; }
    st = add_die(s, "structure_type", 0x130)
    add_attr(s, st, "name", "Point")
    mem_x = add_die(s, "member", 0x131, parent=st)
    add_attr(s, mem_x, "name", "x")
    add_attr(s, mem_x, "type", bt_int.offset)

    # Variable: gVar : int
    var = add_die(s, "variable", 0x140)
    add_attr(s, var, "name", "gVar")
    add_attr(s, var, "type", bt_int.offset)

    # Subprogram: int foo(int a)
    sp = add_die(s, "subprogram", 0x150)
    add_attr(s, sp, "name", "foo")
    add_attr(s, sp, "type", bt_int.offset)  # return type
    fp_a = add_die(s, "formal_parameter", 0x151, parent=sp)
    add_attr(s, fp_a, "name", "a")
    add_attr(s, fp_a, "type", bt_int.offset)

    # Top compile unit DIE to serve as root
    cu = add_die(s, "compile_unit", 0x10)
    # attach interesting top-level DIEs as children of CU
    for child in (td, en, st, var, sp):
        child.parent = cu
    s.flush()
    s.commit()

    return db, cu


def test_cgenerator_generate_declarations_simple():
    db, cu = build_sample_db()
    try:
        gen = CGenerator(db.session)
        decls = gen.generate_declarations(cu)
        assert isinstance(decls, dict)
        assert len(decls.get("typedefs", [])) == 1
        assert len(decls.get("enums", [])) == 1
        assert len(decls.get("records", [])) == 1
        assert len(decls.get("variables", [])) == 1
        assert len(decls.get("functions", [])) == 1

        td = decls["typedefs"][0]
        assert td["name"] == "MyInt"
        assert td["target"] in ("int", "base_type")  # name preferred

        en = decls["enums"][0]
        assert en["name"] == "Color"
        names = [n for (n, v) in en["items"]]
        assert names == ["RED", "GREEN"]

        rec = decls["records"][0]
        assert rec["name"] == "Point"
        assert any(m["name"] == "x" and m["type"] in ("int", "base_type") for m in rec["members"])  # type name preferred

        var = decls["variables"][0]
        assert var["name"] == "gVar"
        assert var["type"] in ("int", "base_type")

        fn = decls["functions"][0]
        assert fn["name"] == "foo"
        assert fn["returns"] in ("int", "base_type")
        assert len(fn["params"]) == 1 and fn["params"][0]["name"] == "a"
    finally:
        db.close()


def test_cgenerator_generate_header_contains_expected_decls(tmp_path):
    db, cu = build_sample_db()
    try:
        gen = CGenerator(db.session)
        header = gen.generate_header(cu, header_name="demo.h")
        # Validate key lines
        assert "#ifndef _DEMO_H_" in header or "#ifndef _DEMO_H" in header
        assert "typedef int MyInt;" in header or "typedef base_type MyInt;" in header
        assert "typedef enum Color" in header
        assert "RED = 0x0" in header and "GREEN = 0x1" in header
        assert "typedef struct Point" in header
        # member declaration line
        assert ("int x;" in header) or ("base_type x;" in header)
        # extern var
        assert ("extern int gVar;" in header) or ("extern base_type gVar;" in header)
        # function prototype
        assert ("int foo(int a);" in header) or ("base_type foo(base_type a);" in header)
    finally:
        db.close()


def test_inline_anonymous_union_rendering():
    # Build DB with struct S containing anonymous union member 'u'
    db = elf_model.Model(":memory:")
    s = db.session

    # Base types
    bt_void = add_die(s, "unspecified_type", 0x200)
    add_attr(s, bt_void, "name", "void")
    bt_ubase = add_die(s, "base_type", 0x201)
    add_attr(s, bt_ubase, "name", "UBaseType_t")

    # pointer to void
    ptr_void = add_die(s, "pointer_type", 0x210)
    add_attr(s, ptr_void, "type", bt_void.offset)

    # anonymous union type with two members
    uanon = add_die(s, "union_type", 0x220)
    # members of union
    um1 = add_die(s, "member", 0x221, parent=uanon)
    add_attr(s, um1, "name", "pvDummy2")
    add_attr(s, um1, "type", ptr_void.offset)
    um2 = add_die(s, "member", 0x222, parent=uanon)
    add_attr(s, um2, "name", "uxDummy2")
    add_attr(s, um2, "type", bt_ubase.offset)

    # struct containing a member 'u' of anonymous union type
    sstruct = add_die(s, "structure_type", 0x230)
    add_attr(s, sstruct, "name", "xSTATIC_QUEUE")
    sm1 = add_die(s, "member", 0x231, parent=sstruct)
    add_attr(s, sm1, "name", "u")
    add_attr(s, sm1, "type", uanon.offset)

    # CU
    cu = add_die(s, "compile_unit", 0x20)
    sstruct.parent = cu
    s.flush()
    s.commit()

    gen = CGenerator(db.session)
    header = gen.generate_header(cu, header_name="x.h")

    # Should render inline union inside struct and not emit standalone anonymous union typedef
    assert "typedef union <anon" not in header
    assert "typedef struct xSTATIC_QUEUE" in header
    # Check inline block lines
    assert "union {" in header
    assert ("void * pvDummy2;" in header) or ("<elem> * pvDummy2;" in header) or ("void * pvDummy2" in header)
    assert "UBaseType_t uxDummy2;" in header
    assert "} u;" in header

    db.close()
