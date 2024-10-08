#!/usr/bin/env python

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2024 by Christoph Schueler <github.com/Christoph2,
                                        cpu12.gems@googlemail.com>

   All Rights Reserved

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from enum import IntEnum


class EnumBase(IntEnum):
    """
    def __init__(self, value):
        self._value = value

    def _getValue(self):
        return self._value

    def __str__(self):
        return "{0!s}".format((self.MAP.get(self._value, self._value)))

    __repr__ = __str__

    value = property(_getValue)
    """

    def __contains__(self, value: int) -> bool:
        return value in self.__members__.values()


class Tag(EnumBase):
    padding = 0x0
    array_type = 0x1
    class_type = 0x2
    entry_point = 0x3
    enumeration_type = 0x4
    formal_parameter = 0x5
    imported_declaration = 0x8
    label = 0xA
    lexical_block = 0xB
    member = 0xD
    pointer_type = 0xF
    reference_type = 0x10
    compile_unit = 0x11
    string_type = 0x12
    structure_type = 0x13
    subroutine_type = 0x15
    typedef = 0x16
    union_type = 0x17
    unspecified_parameters = 0x18
    variant = 0x19
    common_block = 0x1A
    common_inclusion = 0x1B
    inheritance = 0x1C
    inlined_subroutine = 0x1D
    module = 0x1E
    ptr_to_member_type = 0x1F
    set_type = 0x20
    subrange_type = 0x21
    with_stmt = 0x22
    access_declaration = 0x23
    base_type = 0x24
    catch_block = 0x25
    const_type = 0x26
    constant = 0x27
    enumerator = 0x28
    file_type = 0x29
    friend = 0x2A
    namelist = 0x2B
    namelist_item = 0x2C
    packed_type = 0x2D
    subprogram = 0x2E
    template_type_param = 0x2F
    template_value_param = 0x30
    thrown_type = 0x31
    try_block = 0x32
    variant_part = 0x33
    variable = 0x34
    volatile_type = 0x35
    dwarf_procedure = 0x36
    restrict_type = 0x37
    interface_type = 0x38
    namespace = 0x39
    imported_module = 0x3A
    unspecified_type = 0x3B
    partial_unit = 0x3C
    imported_unit = 0x3D
    condition = 0x3F
    shared_type = 0x40
    type_unit = 0x41
    rvalue_reference_type = 0x42
    template_alias = 0x43
    atomic_type = 0x47
    lo_user = 0x4080
    hi_user = 0xFFFF
    MIPS_loop = 0x4081
    HP_array_descriptor = 0x4090
    HP_Bliss_field = 0x4091
    HP_Bliss_field_set = 0x4092
    format_label = 0x4101
    function_template = 0x4102
    class_template = 0x4103
    GNU_BINCL = 0x4104
    GNU_EINCL = 0x4105
    GNU_template_template_param = 0x4106
    GNU_template_parameter_pack = 0x4107
    GNU_formal_parameter_pack = 0x4108
    GNU_call_site = 0x4109
    GNU_call_site_parameter = 0x410A
    upc_shared_type = 0x8765
    upc_strict_type = 0x8766
    upc_relaxed_type = 0x8767
    PGI_kanji_type = 0xA000
    PGI_interface_block = 0xA020

    @classmethod
    def _missing_(cls, value):
        return value


class Children(EnumBase):
    DW_CHILDREN_no = 0x00
    DW_CHILDREN_yes = 0x01


class AttributeEncoding(EnumBase):
    sibling = 0x1
    location = 0x2
    name = 0x3
    ordering = 0x9
    subscr_data = 0xA
    byte_size = 0xB
    bit_offset = 0xC
    bit_size = 0xD
    element_list = 0xF
    stmt_list = 0x10
    low_pc = 0x11
    high_pc = 0x12
    language = 0x13
    member = 0x14
    discr = 0x15
    discr_value = 0x16
    visibility = 0x17
    import_ = 0x18
    string_length = 0x19
    common_reference = 0x1A
    comp_dir = 0x1B
    const_value = 0x1C
    containing_type = 0x1D
    default_value = 0x1E
    inline = 0x20
    is_optional = 0x21
    lower_bound = 0x22
    producer = 0x25
    prototyped = 0x27
    return_addr = 0x2A
    start_scope = 0x2C
    bit_stride = 0x2E
    upper_bound = 0x2F
    abstract_origin = 0x31
    accessibility = 0x32
    address_class = 0x33
    artificial = 0x34
    base_types = 0x35
    calling_convention = 0x36
    count = 0x37
    data_member_location = 0x38
    decl_column = 0x39
    decl_file = 0x3A
    decl_line = 0x3B
    declaration = 0x3C
    discr_list = 0x3D
    encoding = 0x3E
    external = 0x3F
    frame_base = 0x40
    friend = 0x41
    identifier_case = 0x42
    macro_info = 0x43
    namelist_item = 0x44
    priority = 0x45
    segment = 0x46
    specification = 0x47
    static_link = 0x48
    type = 0x49
    use_location = 0x4A
    variable_parameter = 0x4B
    virtuality = 0x4C
    vtable_elem_location = 0x4D
    allocated = 0x4E
    associated = 0x4F
    data_location = 0x50
    byte_stride = 0x51
    entry_pc = 0x52
    use_UTF8 = 0x53
    extension = 0x54
    ranges = 0x55
    trampoline = 0x56
    call_column = 0x57
    call_file = 0x58
    call_line = 0x59
    description = 0x5A
    binary_scale = 0x5B
    decimal_scale = 0x5C
    small = 0x5D
    decimal_sign = 0x5E
    digit_count = 0x5F
    picture_string = 0x60
    mutable = 0x61
    threads_scaled = 0x62
    explicit = 0x63
    object_pointer = 0x64
    endianity = 0x65
    elemental = 0x66
    pure = 0x67
    recursive = 0x68
    signature = 0x69
    main_subprogram = 0x6A
    data_bit_offset = 0x6B
    const_expr = 0x6C
    enum_class = 0x6D
    linkage_name = 0x6E
    string_length_bit_size = 0x6F
    string_length_byte_size = 0x70
    rank = 0x71
    str_offsets_base = 0x72
    addr_base = 0x73
    rnglists_base = 0x74
    dwo_name = 0x76
    reference = 0x77
    rvalue_reference = 0x78
    macros = 0x79
    call_all_calls = 0x7A
    call_all_source_calls = 0x7B
    call_all_tail_calls = 0x7C
    call_return_pc = 0x7D
    call_value = 0x7E
    call_origin = 0x7F
    call_parameter = 0x80
    call_pc = 0x81
    call_tail_call = 0x82
    call_target = 0x83
    call_target_clobbered = 0x84
    call_data_location = 0x85
    call_data_value = 0x86
    noreturn = 0x87
    alignment = 0x88
    export_symbols = 0x89
    deleted = 0x8A
    defaulted = 0x8B
    loclists_base = 0x8C

    lo_user = 0x2000
    hi_user = 0x3FFF
    MIPS_fde = 0x2001
    MIPS_loop_begin = 0x2002
    MIPS_tail_loop_begin = 0x2003
    MIPS_epilog_begin = 0x2004
    MIPS_loop_unroll_factor = 0x2005
    MIPS_software_pipeline_depth = 0x2006
    MIPS_linkage_name = 0x2007
    MIPS_stride = 0x2008
    MIPS_abstract_name = 0x2009
    MIPS_clone_origin = 0x200A
    MIPS_has_inlines = 0x200B
    HP_block_index = 0x2000
    HP_unmodifiable = 0x2001
    HP_prologue = 0x2005
    HP_epilogue = 0x2008
    HP_actuals_stmt_list = 0x2010
    HP_proc_per_section = 0x2011
    HP_raw_data_ptr = 0x2012
    HP_pass_by_reference = 0x2013
    HP_opt_level = 0x2014
    HP_prof_version_id = 0x2015
    HP_opt_flags = 0x2016
    HP_cold_region_low_pc = 0x2017
    HP_cold_region_high_pc = 0x2018
    HP_all_variables_modifiable = 0x2019
    HP_linkage_name = 0x201A
    HP_prof_flags = 0x201B
    HP_unit_name = 0x201F
    HP_unit_size = 0x2020
    HP_widened_byte_size = 0x2021
    HP_definition_points = 0x2022
    HP_default_location = 0x2023
    HP_is_result_param = 0x2029
    sf_names = 0x2101
    src_info = 0x2102
    mac_info = 0x2103
    src_coords = 0x2104
    body_begin = 0x2105
    body_end = 0x2106
    GNU_vector = 0x2107
    GNU_guarded_by = 0x2108
    GNU_pt_guarded_by = 0x2109
    GNU_guarded = 0x210A
    GNU_pt_guarded = 0x210B
    GNU_locks_excluded = 0x210C
    GNU_exclusive_locks_required = 0x210D
    GNU_shared_locks_required = 0x210E
    GNU_odr_signature = 0x210F
    GNU_template_name = 0x2110
    GNU_call_site_value = 0x2111
    GNU_call_site_data_value = 0x2112
    GNU_call_site_target = 0x2113
    GNU_call_site_target_clobbered = 0x2114
    GNU_tail_call = 0x2115
    GNU_all_tail_call_sites = 0x2116
    GNU_all_call_sites = 0x2117
    GNU_all_source_call_sites = 0x2118
    GNU_macros = 0x2119
    GNU_deleted = 0x211A
    GNU_dwo_name = 0x2130
    GNU_dwo_id = 0x2131
    GNU_ranges_base = 0x2132
    GNU_addr_base = 0x2133
    GNU_pubnames = 0x2134
    GNU_pubtypes = 0x2135
    GNU_discriminator = 0x2136
    VMS_rtnbeg_pd_address = 0x2201
    use_GNAT_descriptive_type = 0x2301
    GNAT_descriptive_type = 0x2302
    GNU_numerator = 0x2303
    GNU_denominator = 0x2304
    GNU_bias = 0x2305
    upc_threads_scaled = 0x3210
    PGI_lbase = 0x3A00
    PGI_soffset = 0x3A01
    PGI_lstride = 0x3A02
    PPLE_optimized = 0x3FE1
    PPLE_flags = 0x3FE2
    PPLE_isa = 0x3FE3
    PPLE_block = 0x3FE4
    PPLE_major_runtime_vers = 0x3FE5
    PPLE_runtime_class = 0x3FE6
    PPLE_omit_frame_ptr = 0x3FE7
    PPLE_property_name = 0x3FE8
    PPLE_property_getter = 0x3FE9
    PPLE_property_setter = 0x3FEA
    PPLE_property_attribute = 0x3FEB
    PPLE_objc_complete_type = 0x3FEC
    PPLE_property = 0x3FED

    UNKOWN = 0xFFFF

    @classmethod
    def _missing_(cls, value):
        return f"Unknown AT value (0x{value:04x})"


class FakeEncoding:

    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @property
    def name(self):
        return f"Unknown AT value (0x{self._value:04x})"


class AttributeForm(EnumBase):
    # MAP = FORM_MAP
    ##
    ## Attribute form encodings.
    ##
    DW_FORM_addr = 0x01
    DW_FORM_block2 = 0x03
    DW_FORM_block4 = 0x04
    DW_FORM_data2 = 0x05
    DW_FORM_data4 = 0x06
    DW_FORM_data8 = 0x07
    DW_FORM_string = 0x08
    DW_FORM_block = 0x09
    DW_FORM_block1 = 0x0A
    DW_FORM_data1 = 0x0B
    DW_FORM_flag = 0x0C
    DW_FORM_sdata = 0x0D
    DW_FORM_strp = 0x0E
    DW_FORM_udata = 0x0F
    DW_FORM_ref_addr = 0x10
    DW_FORM_ref1 = 0x11
    DW_FORM_ref2 = 0x12
    DW_FORM_ref4 = 0x13
    DW_FORM_ref8 = 0x14
    DW_FORM_ref_udata = 0x15
    DW_FORM_indirect = 0x16
    DW_FORM_sec_offset = 0x17
    DW_FORM_exprloc = 0x18
    DW_FORM_flag_present = 0x19

    DW_FORM_line_strp = 0x1F

    """
    DW_FORM_strx = 0x1a
    DW_FORM_addrx = 0x1b
    DW_FORM_ref_sup4 = 0x1c
    DW_FORM_strp_sup = 0x1d
    DW_FORM_data16 = 0x1e
    """

    DW_FORM_ref_sig8 = 0x20
    DW_FORM_implicit_const = 0x21
    """
    DW_FORM_loclistx ‡
    0x22
    loclist
    DW_FORM_rnglistx ‡
    0x23
    rnglist
    DW_FORM_ref_sup8 ‡
    0x24
    reference
    DW_FORM_strx1 ‡
    0x25
    string
    DW_FORM_strx2 ‡
    0x26
    string
    DW_FORM_strx3 ‡
    0x27
    string
    DW_FORM_strx4 ‡
    0x28
    string
    DW_FORM_addrx1 ‡
    0x29
    address
    DW_FORM_addrx2 ‡
    0x2a
    address
    DW_FORM_addrx3 ‡
    0x2b
    address
    DW_FORM_addrx4 ‡
    0x2c
    address
    """


class UnitHeader(EnumBase):
    DW_UT_compile = 0x01
    DW_UT_type = 0x02
    DW_UT_partial = 0x03
    DW_UT_skeleton = 0x04
    DW_UT_split_compile = 0x05
    DW_UT_split_type = 0x06
    DW_UT_lo_user = 0x80
    DW_UT_hi_user = 0xFF


class Operation(EnumBase):
    addr = 0x3
    deref = 0x6
    const1u = 0x8
    const1s = 0x9
    const2u = 0xA
    const2s = 0xB
    const4u = 0xC
    const4s = 0xD
    const8u = 0xE
    const8s = 0xF
    constu = 0x10
    consts = 0x11
    dup = 0x12
    drop = 0x13
    over = 0x14
    pick = 0x15
    swap = 0x16
    rot = 0x17
    xderef = 0x18
    abs = 0x19
    and_ = 0x1A
    div = 0x1B
    minus = 0x1C
    mod = 0x1D
    mul = 0x1E
    neg = 0x1F
    not_ = 0x20
    or_ = 0x21
    plus = 0x22
    plus_uconst = 0x23
    shl = 0x24
    shr = 0x25
    shra = 0x26
    xor = 0x27
    bra = 0x28
    eq = 0x29
    ge = 0x2A
    gt = 0x2B
    le = 0x2C
    lt = 0x2D
    ne = 0x2E
    skip = 0x2F
    lit0 = 0x30
    lit1 = 0x31
    lit2 = 0x32
    lit3 = 0x33
    lit4 = 0x34
    lit5 = 0x35
    lit6 = 0x36
    lit7 = 0x37
    lit8 = 0x38
    lit9 = 0x39
    lit10 = 0x3A
    lit11 = 0x3B
    lit12 = 0x3C
    lit13 = 0x3D
    lit14 = 0x3E
    lit15 = 0x3F
    lit16 = 0x40
    lit17 = 0x41
    lit18 = 0x42
    lit19 = 0x43
    lit20 = 0x44
    lit21 = 0x45
    lit22 = 0x46
    lit23 = 0x47
    lit24 = 0x48
    lit25 = 0x49
    lit26 = 0x4A
    lit27 = 0x4B
    lit28 = 0x4C
    lit29 = 0x4D
    lit30 = 0x4E
    lit31 = 0x4F
    reg0 = 0x50
    reg1 = 0x51
    reg2 = 0x52
    reg3 = 0x53
    reg4 = 0x54
    reg5 = 0x55
    reg6 = 0x56
    reg7 = 0x57
    reg8 = 0x58
    reg9 = 0x59
    reg10 = 0x5A
    reg11 = 0x5B
    reg12 = 0x5C
    reg13 = 0x5D
    reg14 = 0x5E
    reg15 = 0x5F
    reg16 = 0x60
    reg17 = 0x61
    reg18 = 0x62
    reg19 = 0x63
    reg20 = 0x64
    reg21 = 0x65
    reg22 = 0x66
    reg23 = 0x67
    reg24 = 0x68
    reg25 = 0x69
    reg26 = 0x6A
    reg27 = 0x6B
    reg28 = 0x6C
    reg29 = 0x6D
    reg30 = 0x6E
    reg31 = 0x6F
    breg0 = 0x70
    breg1 = 0x71
    breg2 = 0x72
    breg3 = 0x73
    breg4 = 0x74
    breg5 = 0x75
    breg6 = 0x76
    breg7 = 0x77
    breg8 = 0x78
    breg9 = 0x79
    breg10 = 0x7A
    breg11 = 0x7B
    breg12 = 0x7C
    breg13 = 0x7D
    breg14 = 0x7E
    breg15 = 0x7F
    breg16 = 0x80
    breg17 = 0x81
    breg18 = 0x82
    breg19 = 0x83
    breg20 = 0x84
    breg21 = 0x85
    breg22 = 0x86
    breg23 = 0x87
    breg24 = 0x88
    breg25 = 0x89
    breg26 = 0x8A
    breg27 = 0x8B
    breg28 = 0x8C
    breg29 = 0x8D
    breg30 = 0x8E
    breg31 = 0x8F
    regx = 0x90
    fbreg = 0x91
    bregx = 0x92
    piece = 0x93
    deref_size = 0x94
    xderef_size = 0x95
    nop = 0x96
    push_object_address = 0x97
    call2 = 0x98
    call4 = 0x99
    call_ref = 0x9A
    form_tls_address = 0x9B
    call_frame_cfa = 0x9C
    bit_piece = 0x9D
    implicit_value = 0x9E
    stack_value = 0x9F
    implicit_pointer = 0xA0
    addrx = 0xA1
    constx = 0xA2

    entry_value = 0xA3
    const_type = 0xA4
    regval_type = 0xA5
    deref_type = 0xA6
    xderef_type = 0xA7
    convert = 0xA8
    reinterpret = 0xA9

    lo_user = 0xE0
    hi_user = 0xFF
    GNU_push_tls_address = 0xE0
    GNU_uninit = 0xF0
    GNU_encoded_addr = 0xF1
    GNU_implicit_pointer = 0xF2

    GNU_entry_value = 0xF3
    GNU_const_type = 0xF4
    GNU_regval_type = 0xF5
    GNU_deref_type = 0xF6
    GNU_convert = 0xF7
    GNU_reinterpret = 0xF9

    GNU_parameter_ref = 0xFA
    GNU_addr_index = 0xFB
    GNU_const_index = 0xFC
    HP_unknown = 0xE0
    HP_is_value = 0xE1
    HP_fltconst4 = 0xE2
    HP_fltconst8 = 0xE3
    HP_mod_range = 0xE4
    HP_unmod_range = 0xE5
    HP_tls = 0xE6
    GI_omp_thread_num = 0xF8


class BaseTypeEncoding(EnumBase):
    void = 0x0
    address = 0x1
    boolean = 0x2
    complex_float = 0x3
    float = 0x4
    signed = 0x5
    signed_char = 0x6
    unsigned = 0x7
    unsigned_char = 0x8
    imaginary_float = 0x9
    packed_decimal = 0xA
    numeric_string = 0xB
    edited = 0xC
    signed_fixed = 0xD
    unsigned_fixed = 0xE
    decimal_float = 0xF
    UTF = 0x10
    lo_user = 0x80
    hi_user = 0xFF
    HP_float80 = 0x80
    HP_complex_float80 = 0x81
    HP_float128 = 0x82
    HP_complex_float128 = 0x83
    HP_floathpintel = 0x84
    HP_imaginary_float80 = 0x85
    HP_imaginary_float128 = 0x86
    HP_VAX_float = 0x88
    HP_VAX_float_d = 0x89
    HP_packed_decimal = 0x8A
    HP_zoned_decimal = 0x8B
    HP_edited = 0x8C
    HP_signed_fixed = 0x8D
    HP_unsigned_fixed = 0x8E
    HP_VAX_complex_float = 0x8F
    HP_VAX_complex_float_d = 0x90


class DecimalSign(EnumBase):
    unsigned = 0x01
    leading_overpunch = 0x02
    trailing_overpunch = 0x03
    leading_separate = 0x04
    trailing_separate = 0x05


class Endianity(EnumBase):
    default = 0x00
    big = 0x01
    little = 0x02
    lo_user = 0x40
    hi_user = 0xFF


class Accessibility(EnumBase):
    public = 0x01
    protected = 0x02
    private = 0x03


class Visibility(EnumBase):
    local = 0x01
    exported = 0x02
    qualified = 0x03


class Virtuality(EnumBase):
    none = 0x00
    virtual = 0x01
    pure_virtual = 0x02


class IdentifierCase(EnumBase):
    case_sensitive = 0x00
    up_case = 0x01
    down_case = 0x02
    case_insensitive = 0x03


class CallingConvention(EnumBase):
    normal = 0x01
    program = 0x02
    nocall = 0x03
    renesas_sh = 0x40
    borland_fastcall_i386 = 0x41
    thiscall_i386 = 0x42
    lo_user = 0x60
    hi_user = 0xFF


class Inline(EnumBase):
    not_inlined = 0x00
    inlined = 0x01
    declared_not_inlined = 0x02
    declared_inlined = 0x03


class Ordering(EnumBase):
    row_major = 0x00
    col_major = 0x01


class DiscriminantDescriptor(EnumBase):
    label = 0x00
    range = 0x01


class LineNumberStandard(EnumBase):
    DW_LNS_copy = 0x01
    DW_LNS_advance_pc = 0x02
    DW_LNS_advance_line = 0x03
    DW_LNS_set_file = 0x04
    DW_LNS_set_column = 0x05
    DW_LNS_negate_stmt = 0x06
    DW_LNS_set_basic_block = 0x07
    DW_LNS_const_add_pc = 0x08
    DW_LNS_fixed_advance_pc = 0x09
    DW_LNS_set_prologue_end = 0x0A
    DW_LNS_set_epilogue_begin = 0x0B
    DW_LNS_set_isa = 0x0C


class LineNumberExtended(EnumBase):
    DW_LNE_end_sequence = 0x01
    DW_LNE_set_address = 0x02
    DW_LNE_define_file = 0x03
    DW_LNE_set_discriminator = 0x04
    DW_LNE_lo_user = 0x80
    DW_LNE_hi_user = 0xFF


class MacroInformation(EnumBase):
    DW_MACINFO_define = 0x01
    DW_MACINFO_undef = 0x02
    DW_MACINFO_start_file = 0x03
    DW_MACINFO_end_file = 0x04
    DW_MACINFO_vendor_ext = 0xFF


##
## Segmented Addresses.
##

# For example, the Intel386 processor might use the following values:

DW_ADDR_none = 0x00
DW_ADDR_near16 = 0x01
DW_ADDR_far16 = 0x02
DW_ADDR_huge16 = 0x03
DW_ADDR_near32 = 0x04
DW_ADDR_far32 = 0x05


class ExceptionHeaderEncoding(EnumBase):
    """The DWARF Exception Header Encoding is used to describe the type of data
    used in the .eh_frame and .eh_frame_hdr section.

    Linux specific, s. Linux Base Standard.
    """

    DW_EH_PE_absptr = 0x00
    DW_EH_PE_uleb128 = 0x01
    DW_EH_PE_udata2 = 0x02
    DW_EH_PE_udata4 = 0x03
    DW_EH_PE_udata8 = 0x04
    DW_EH_PE_sleb128 = 0x09
    DW_EH_PE_sdata2 = 0x0A
    DW_EH_PE_sdata4 = 0x0B
    DW_EH_PE_sdata8 = 0x0C
    DW_EH_PE_pcrel = 0x10
    DW_EH_PE_textrel = 0x20
    DW_EH_PE_datarel = 0x30
    DW_EH_PE_funcrel = 0x40
    DW_EH_PE_aligned = 0x50


class CFIExtensions(EnumBase):
    """ """

    DW_CFA_GNU_args_size = 0x2E
    DW_CFA_GNU_negative_offset_extended = 0x2F


class Languages(EnumBase):
    """ """

    C89 = 0x0001
    C = 0x0002
    Ada83 = 0x0003
    C_plus_plus = 0x0004
    Cobol74 = 0x0005
    Cobol85 = 0x0006
    Fortran77 = 0x0007
    Fortran90 = 0x0008
    Pascal83 = 0x0009
    Modula2 = 0x000A
    Java = 0x000B
    C99 = 0x000C
    Ada95 = 0x000D
    Fortran95 = 0x000E
    PLI = 0x000F
    ObjC = 0x0010
    ObjC_plus_plus = 0x0011
    UPC = 0x0012
    D = 0x0013
    Python = 0x0014
    OpenCL = 0x0015
    Go = 0x0016
    Modula3 = 0x0017
    Haskell = 0x0018
    C_plus_plus_03 = 0x0019
    C_plus_plus_11 = 0x001A
    OCaml = 0x001B
    Rust = 0x001C
    C11 = 0x001D
    Swift = 0x001E
    Julia = 0x001F
    Dylan = 0x0020
    C_plus_plus_14 = 0x0021
    Fortran03 = 0x0022
    Fortran08 = 0x0023
    RenderScript = 0x0024
    BLISS = 0x0025
    Kotlin = 0x0026
    Zig = 0x0027
    Crystal = 0x0028
    C_plus_plus_17 = 0x002A
    C_plus_plus_20 = 0x002B
    C17 = 0x002C
    Fortran18 = 0x002D
    Ada2005 = 0x002E
    Ada2012 = 0x002F
    HIP = 0x0030
    Assembly = 0x0031
    C_sharp = 0x0032
    Mojo = 0x0033
    GLSL = 0x0034
    GLSL_ES = 0x0035
    HLSL = 0x0036
    OpenCL_CPP = 0x0037
    CPP_for_OpenCL = 0x0038
    SYCL = 0x0039
    Ruby = 0x0040
    Move = 0x0041
    Hylo = 0x0042

    Mips_Assembler = 0x8001
    GOOGLE_RenderScript = 0x8E57
    BORLAND_Delphi = 0xB000


class Defaulted(EnumBase):
    DW_DEFAULTED_no = 0x00
    DW_DEFAULTED_in_class = 0x01
    DW_DEFAULTED_out_of_class = 0x02
