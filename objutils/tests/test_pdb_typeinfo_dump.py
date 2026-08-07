from objutils import symbols
from objutils.pecoff.pdb import (
    BasicType,
    CTypeInfoDump,
    DataKind,
    IMAGEHLP_SYMBOL_TYPE_INFO,
    SymTagEnum,
    UdtKind,
)


class StubTypeInfoDump(CTypeInfoDump):
    def __init__(self, payload):
        super().__init__(None, 0)
        self.payload = payload

    def get_type_info(self, type_id, info_type):
        return self.payload.get((type_id, info_type))


def test_get_full_type_name_resolves_struct_members():
    payload = {
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagBaseType,
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_BASETYPE): BasicType.btInt,
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_LENGTH): 4,
        (10, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagUDT,
        (10, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_UDTKIND): UdtKind.UdtStruct,
        (10, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME): "S",
        (10, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_LENGTH): 8,
        (10, IMAGEHLP_SYMBOL_TYPE_INFO.TI_FINDCHILDREN): [11, 12],
        (11, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagData,
        (11, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME): "a",
        (11, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPE): 1,
        (11, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_DATAKIND): DataKind.DataIsMember,
        (11, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_OFFSET): 0,
        (12, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagData,
        (12, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME): "b",
        (12, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPE): 1,
        (12, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_DATAKIND): DataKind.DataIsMember,
        (12, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_OFFSET): 4,
    }
    dumper = StubTypeInfoDump(payload)

    result = dumper.get_full_type_name(10)

    assert isinstance(result, symbols.StructureType)
    assert result.name == "S"
    assert result.byte_size == 8
    assert [(m.name, m.offset) for m in result.member] == [("a", 0), ("b", 4)]
    assert all(isinstance(m.type, symbols.PrimitiveType) for m in result.member)


def test_get_full_type_name_resolves_enum_and_typedef():
    payload = {
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagBaseType,
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_BASETYPE): BasicType.btInt,
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_LENGTH): 4,
        (20, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagEnum,
        (20, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME): "MyEnum",
        (20, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_LENGTH): 4,
        (20, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPE): 1,
        (20, IMAGEHLP_SYMBOL_TYPE_INFO.TI_FINDCHILDREN): [21, 22],
        (21, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagData,
        (21, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME): "A",
        (21, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPE): 1,
        (21, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_DATAKIND): DataKind.DataIsConstant,
        (21, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_VALUE): 1,
        (22, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagData,
        (22, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME): "B",
        (22, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPE): 1,
        (22, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_DATAKIND): DataKind.DataIsConstant,
        (22, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_VALUE): 2,
        (30, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagTypedef,
        (30, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME): "EnumAlias",
        (30, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPE): 20,
    }
    dumper = StubTypeInfoDump(payload)

    result = dumper.get_full_type_name(30)

    assert isinstance(result, symbols.TypeDefinition)
    assert result.name == "EnumAlias"
    assert isinstance(result.type, symbols.EnumerationType)
    assert [e.name for e in result.type.enumerators] == ["A", "B"]
    assert [e.value for e in result.type.enumerators] == [1, 2]


def test_get_full_type_name_resolves_function_signature():
    payload = {
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagBaseType,
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_BASETYPE): BasicType.btInt,
        (1, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_LENGTH): 4,
        (2, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagPointerType,
        (2, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPEID): 1,
        (2, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_REFERENCE): False,
        (40, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagFunctionType,
        (40, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME): "fn_t",
        (40, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPEID): 1,
        (40, IMAGEHLP_SYMBOL_TYPE_INFO.TI_FINDCHILDREN): [41],
        (41, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagFunctionArgType,
        (41, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPEID): 2,
    }
    dumper = StubTypeInfoDump(payload)

    result = dumper.get_full_type_name(40)

    assert isinstance(result, symbols.SubroutineType)
    assert result.name == "fn_t"
    assert isinstance(result.return_type, symbols.PrimitiveType)
    assert len(result.parameters) == 1
    assert isinstance(result.parameters[0], symbols.PointerType)


def test_get_full_type_name_handles_recursive_reference():
    payload = {
        (50, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG): SymTagEnum.SymTagPointerType,
        (50, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPEID): 50,
        (50, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_REFERENCE): False,
    }
    dumper = StubTypeInfoDump(payload)

    result = dumper.get_full_type_name(50)

    assert isinstance(result, symbols.PointerType)
    assert isinstance(result.type, symbols.UnspecifiedType)
    assert "recursive_type_50" == result.type.name
