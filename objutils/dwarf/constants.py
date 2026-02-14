#!/usr/bin/env python

"""DWARF4 Constants and Enumerations.

This module defines all DWARF4 specification constants and enumerations used for
parsing and manipulating DWARF debug information. It provides a comprehensive set of
IntEnum-based enumerations that map human-readable names to their DWARF4 specification
values.

Module Components:
    - EnumBase: Base class for all DWARF enumerations with membership checking.
    - Tag enums: DWARF debugging information entry (DIE) tag types.
    - Attribute enums: DWARF DIE attribute types and encodings.
    - Form enums: DWARF attribute form encodings.
    - Operation enums: DWARF expression location list opcodes.
    - Type enums: DWARF base type encodings, endianity, accessibility, etc.
    - Line number enums: DWARF line number program encodings.

Enum Categories:
    - Tags: Debugging information entry types (DW_TAG_*).
    - Attributes: DIE attribute names (DW_AT_*).
    - AttributeForms: Attribute data format encodings (DW_FORM_*).
    - Operations: Expression location list operations (DW_OP_*).
    - BaseTypeEncoding: Base type classification and encoding.
    - LineNumber Standard/Extended: Line number program opcodes.
    - Accessibility, Visibility, Virtuality: Class/member properties.
    - CallingConvention, Inline, Ordering: Function and array properties.

EnumBase Pattern:
    The EnumBase class extends IntEnum with a custom __contains__ method to enable
    membership testing against enum values. All enumerations define a _missing_
    classmethod to handle unknown values gracefully rather than raising exceptions.
    This allows the code to work with both standard DWARF constants and vendor-specific
    extensions without breaking on unknown values.

Design Pattern:
    Each enum class represents a complete set of DWARF constants for a specific domain:
    - IntEnum provides integer semantics and comparison operations
    - __contains__ enables efficient membership testing without exceptions
    - _missing_ classmethod handles graceful degradation for unknown values
    - Values are directly from DWARF4 specification

References:
    - DWARF4 Specification: http://www.dwarfstd.org/
    - GNU DWARF Extensions
    - LLVM/Clang extensions
    - Apple (Darwin) extensions
    - Intel, HP, MIPS, IBM, Borland, PGI vendor extensions

Copyright (C) 2010-2025 by Christoph Schueler
"""

from enum import IntEnum


class EnumBase(IntEnum):
    """Base class for DWARF enumerations with enhanced functionality.
    
    Extends IntEnum to provide custom membership testing and graceful handling of
    unknown values. This allows safe interaction with DWARF constants from various
    compiler vendors and DWARF extensions.
    
    The __contains__ method enables efficient testing of whether a value corresponds
    to an enum member. Unknown values are handled by _missing_ classmethod rather than
    raising exceptions.
    
    Example:
        >>> tag = Tag.compile_unit
        >>> 0x11 in tag.__class__  # Check if value 0x11 is a valid Tag
        True
        >>> unknown = Tag(0xFFFF)  # Returns 0xFFFF without error
    """

    def __contains__(self, value: int) -> bool:
        """Check if a value is a member of this enumeration.
        
        Performs membership testing against all enum member values (not names).
        This differs from standard enum behavior and enables safe handling of
        enum values without requiring try/except blocks.
        
        Args:
            value: Integer value to test for membership in this enum.
            
        Returns:
            True if the value corresponds to an enum member, False otherwise.
        """
        return value in self.__members__.values()


class Tag(EnumBase):
    """DWARF Debugging Information Entry Tags.
    
    Defines all possible DW_TAG_* constants that identify the type of debugging
    information contained in a DIE (Debugging Information Entry). Tags specify
    what kind of entity a DIE describes (e.g., compile_unit, subprogram, variable).
    
    Includes standard DWARF4 tags, GNU extensions, and vendor-specific extensions.
    """
    padding = 0x0
    array_type = 0x1
    class_type = 0x2
    entry_point = 0x3
    enumeration_type = 0x4
    formal_parameter = 0x5
    imported_declaration = 0x8
    ordering = 0x09
    label = 0xA
    lexical_block = 0xB
    bit_offset = 0xC
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
    encoding = 0x3E
    condition = 0x3F
    shared_type = 0x40
    type_unit = 0x41
    rvalue_reference_type = 0x42
    template_alias = 0x43
    coarray_type = 0x44
    generic_subrange = 0x45
    dynamic_type = 0x46
    atomic_type = 0x47
    call_site = 0x48
    call_site_parameter = 0x49
    skeleton_unit = 0x4A
    immutable_type = 0x4B

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
    """DWARF DIE Children Indicators.
    
    Specifies whether a Debugging Information Entry (DIE) has child DIEs.
    This two-value enum is used in DIE abbreviations to indicate the presence
    of child DIEs that provide additional details about the parent DIE.
    
    Attributes:
        DW_CHILDREN_no (0x00): DIE has no children.
        DW_CHILDREN_yes (0x01): DIE may have children.
    """
    DW_CHILDREN_no = 0x00
    DW_CHILDREN_yes = 0x01


class AttributeEncoding(EnumBase):
    """DWARF Attribute Name Encodings.
    
    Defines all possible DW_AT_* attribute names that can appear in DIEs.
    These attributes describe properties of the entity represented by a DIE
    (e.g., name, type, location, byte size).
    
    Includes standard DWARF4 attributes and vendor-specific extensions
    (GNU, MIPS, HP, SUN, Apple, LLVM, etc.).
    """
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
    dwo_id = 0x75
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

    language_name = 0x90
    language_version = 0x91

    ghs_namespace_alias = 0x806
    ghs_using_namespace = 0x807
    ghs_using_declaration = 0x808

    HP_block_index = 0x2000

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

    TI_version = 0x200B
    MIPS_stride_byte = 0x200C
    TI_asm = 0x200C
    MIPS_stride_elem = 0x200D
    MIPS_ptr_dopetype = 0x200E
    TI_skeletal = 0x200E
    MIPS_allocatable_dopetype = 0x200F
    MIPS_assumed_shape_dopetype = 0x2010
    MIPS_assumed_size = 0x2011
    TI_interrupt = 0x2011
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
    GNU_locviews = 0x2137
    GNU_entry_view = 0x2138

    SUN_template = 0x2201
    SUN_alignment = 0x2202
    SUN_vtable = 0x2203
    SUN_count_guarantee = 0x2204
    SUN_command_line = 0x2205
    SUN_vbase = 0x2206
    SUN_compile_options = 0x2207
    SUN_language = 0x2208
    SUN_browser_file = 0x2209
    SUN_vtable_abi = 0x2210
    SUN_func_offsets = 0x2211
    SUN_cf_kind = 0x2212
    SUN_vtable_index = 0x2213
    SUN_omp_tpriv_addr = 0x2214
    SUN_omp_child_func = 0x2215
    SUN_func_offset = 0x2216
    SUN_memop_type_ref = 0x2217
    SUN_profile_id = 0x2218
    SUN_memop_signature = 0x2219
    SUN_obj_dir = 0x2220
    SUN_obj_file = 0x2221
    SUN_original_name = 0x2222
    SUN_hwcprof_signature = 0x2223
    SUN_amd64_parmdump = 0x2224
    SUN_part_link_name = 0x2225
    SUN_link_name = 0x2226
    SUN_pass_with_const = 0x2227
    SUN_return_with_const = 0x2228
    SUN_import_by_name = 0x2229
    SUN_f90_pointer = 0x222A
    SUN_pass_by_ref = 0x222B
    SUN_f90_allocatable = 0x222C
    SUN_f90_assumed_shape_array = 0x222D
    SUN_c_vla = 0x222E
    SUN_return_value_ptr = 0x2230
    SUN_dtor_start = 0x2231
    SUN_dtor_length = 0x2232
    SUN_dtor_state_initial = 0x2233
    SUN_dtor_state_final = 0x2234
    SUN_dtor_state_deltas = 0x2235
    SUN_import_by_lname = 0x2236
    SUN_f90_use_only = 0x2237
    SUN_namelist_spec = 0x2238
    SUN_is_omp_child_func = 0x2239
    SUN_fortran_main_alias = 0x223A
    SUN_fortran_based = 0x223B

    ALTIUM_loclist = 0x2300
    use_GNAT_descriptive_type = 0x2301
    GNAT_descriptive_type = 0x2302
    GNU_numerator = 0x2303
    GNU_denominator = 0x2304
    GNU_bias = 0x2305

    go_kind = 0x2900
    go_key = 0x2901
    go_elem = 0x2902
    go_embedded_field = 0x2903
    go_runtime_type = 0x2904

    upc_threads_scaled = 0x3210
    IBM_wsa_addr = 0x393E
    IBM_home_location = 0x393F
    IBM_alt_srcview = 0x3940

    PGI_lbase = 0x3A00
    PGI_soffset = 0x3A01
    PGI_lstride = 0x3A02

    BORLAND_property_read = 0x3B11
    BORLAND_property_write = 0x3B12
    BORLAND_property_implements = 0x3B13
    BORLAND_property_index = 0x3B14
    BORLAND_property_default = 0x3B15
    BORLAND_Delphi_unit = 0x3B20
    BORLAND_Delphi_class = 0x3B21
    BORLAND_Delphi_record = 0x3B22
    BORLAND_Delphi_metaclass = 0x3B23
    BORLAND_Delphi_constructor = 0x3B24
    BORLAND_Delphi_destructor = 0x3B25
    BORLAND_Delphi_anonymous_method = 0x3B26
    BORLAND_Delphi_interface = 0x3B27
    BORLAND_Delphi_ABI = 0x3B28
    BORLAND_Delphi_frameptr = 0x3B30
    BORLAND_closure = 0x3B31

    LLVM_include_path = 0x3E00
    LLVM_config_macros = 0x3E01
    LLVM_sysroot = 0x3E02
    LLVM_tag_offset = 0x3E03
    LLVM_apinotes = 0x3E07
    LLVM_active_lane = 0x3E08
    LLVM_augmentation = 0x3E09
    LLVM_lanes = 0x3E0A
    LLVM_lane_pc = 0x3E0B
    LLVM_vector_size = 0x3E0C

    APPLE_optimized = 0x3FE1
    APPLE_flags = 0x3FE2
    APPLE_isa = 0x3FE3
    APPLE_block = 0x3FE4
    APPLE_major_runtime_vers = 0x3FE5
    APPLE_runtime_class = 0x3FE6
    APPLE_omit_frame_ptr = 0x3FE7
    APPLE_property_name = 0x3FE8
    APPLE_property_getter = 0x3FE9
    APPLE_property_setter = 0x3FEA
    APPLE_property_attribute = 0x3FEB
    APPLE_objc_complete_type = 0x3FEC
    APPLE_property = 0x3FED
    APPLE_objc_direct = 0x3FEE
    APPLE_sdk = 0x3FEF
    APPLE_origin = 0x3FF0

    UNKOWN = 0xFFFF

    @classmethod
    def _missing_(cls, value):
        return f"Unknown AT value (0x{value:04x})"


class FakeEncoding:
    """Placeholder for unknown attribute encoding values.
    
    Used when an unknown DW_AT_* value is encountered to provide a consistent
    interface that can be treated like an AttributeEncoding enum member.
    This allows graceful handling of vendor-specific or future DWARF extensions.
    """
    
    def __init__(self, value: int) -> None:
        """Initialize FakeEncoding with an integer value.
        
        Args:
            value: The unknown attribute encoding value.
        """
        self._value = value

    def __int__(self) -> int:
        """Return the integer value of this encoding."""
        return self._value

    @property
    def value(self) -> int:
        """Get the integer value of this encoding."""
        return self._value

    @property
    def name(self) -> str:
        """Get a string representation of this unknown encoding."""
        return f"Unknown AT value (0x{self._value:04x})"


class AttributeForm(EnumBase):
    """DWARF Attribute Form Encodings.
    
    Defines all possible DW_FORM_* constants that specify how attribute values
    are encoded in a DIE. Forms determine the binary representation of attribute data
    (e.g., address, block, string, constant values). The form is essential for
    correctly parsing attribute values during debug information processing.
    
    Includes standard DWARF4 forms and DWARF5 extensions.
    """
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
    DW_FORM_strx = 0x1A
    DW_FORM_addrx = 0x1B
    DW_FORM_ref_sup4 = 0x1C
    DW_FORM_strp_sup = 0x1D
    DW_FORM_data16 = 0x1E
    DW_FORM_line_strp = 0x1F
    DW_FORM_ref_sig8 = 0x20
    DW_FORM_implicit_const = 0x21
    DW_FORM_loclistx = 0x22
    DW_FORM_rnglistx = 0x23
    DW_FORM_ref_sup8 = 0x24
    DW_FORM_strx1 = 0x25
    DW_FORM_strx2 = 0x26
    DW_FORM_strx3 = 0x27
    DW_FORM_strx4 = 0x28
    DW_FORM_addrx1 = 0x29
    DW_FORM_addrx2 = 0x2A
    DW_FORM_addrx3 = 0x2B
    DW_FORM_addrx4 = 0x2C


class UnitHeader(EnumBase):
    """DWARF Unit Header Type Encodings.
    
    Defines DW_UT_* constants that specify the type of compilation unit in DWARF5.
    Each unit type indicates the purpose and structure of the compilation unit data
    (e.g., compile_unit, type_unit, partial_unit).
    
    Attributes:
        DW_UT_compile (0x01): Standard compilation unit.
        DW_UT_type (0x02): Type unit for shared type definitions.
        DW_UT_partial (0x03): Partial compilation unit.
        DW_UT_skeleton (0x04): Skeleton unit for split DWARF.
        DW_UT_split_compile (0x05): Split compilation unit.
        DW_UT_split_type (0x06): Split type unit.
    """
    DW_UT_compile = 0x01
    DW_UT_type = 0x02
    DW_UT_partial = 0x03
    DW_UT_skeleton = 0x04
    DW_UT_split_compile = 0x05
    DW_UT_split_type = 0x06
    DW_UT_lo_user = 0x80
    DW_UT_hi_user = 0xFF


class Operation(EnumBase):
    """DWARF Expression Location List Opcodes.
    
    Defines DW_OP_* constants that represent operations in DWARF expressions and
    location descriptions. These opcodes form a stack-based language for specifying
    how to compute values (e.g., variable locations, register contents).
    
    Includes standard DWARF4 operations, GNU extensions, LLVM extensions, and WASM support.
    Operations manipulate a stack of values and include arithmetic, logical, comparison,
    memory access, and control flow operations.
    
    Categories:
        - Literals: Push values onto stack (lit0-lit31, const1u/s, etc.)
        - Registers: Push register values (reg0-reg31, regx, etc.)
        - Memory: Dereference stack values (deref, deref_size, xderef, etc.)
        - Arithmetic: Add, subtract, multiply, divide, etc.
        - Logical: AND, OR, XOR, NOT operations
        - Comparison: EQ, LT, GT, LE, GE, NE comparisons
        - Control: Branch, skip, etc.
        - Specialized: TLS, CFA, CFI, etc.
    """
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

    GNU_push_tls_address = 0xE0
    LLVM_form_aspace_address = 0xE1
    LLVM_push_lane = 0xE2
    LLVM_offset = 0xE3
    LLVM_offset_uconst = 0xE4
    LLVM_bit_offset = 0xE5
    LLVM_call_frame_entry_reg = 0xE6
    LLVM_undefined = 0xE7
    LLVM_aspace_bregx = 0xE8
    LLVM_aspace_implicit_pointer = 0xE9
    LLVM_piece_end = 0xEA
    LLVM_extend = 0xEB
    LLVM_select_bit_piece = 0xEC
    WASM_location = 0xED
    WASM_location_int = 0xEE

    GNU_uninit = 0xF0
    GNU_encoded_addr = 0xF1
    GNU_implicit_pointer = 0xF2
    GNU_entry_value = 0xF3
    GNU_const_type = 0xF4
    GNU_regval_type = 0xF5
    GNU_deref_type = 0xF6
    GNU_convert = 0xF7
    PGI_omp_thread_num = 0xF8
    GNU_reinterpret = 0xF9
    GNU_parameter_ref = 0xFA
    GNU_addr_index = 0xFB
    GNU_const_index = 0xFC
    lo_user = 0xFF
    hi_user = 0xFFFF


class BaseTypeEncoding(EnumBase):
    """DWARF Base Type Encodings.
    
    Defines DW_ATE_* constants that specify the encoding of base types. These values
    describe the fundamental type classification (e.g., signed integer, floating-point,
    boolean) used in type information.
    
    Includes standard DWARF4 encodings, HP floating-point extensions, and more.
    
    Attributes:
        void, address, boolean, complex_float, float, signed, unsigned, etc.
    """
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
    UCS = 0x11
    ASCII = 0x12
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
    """DWARF Decimal Sign Encodings.
    
    Defines DW_DS_* constants that specify how signs are represented in decimal types.
    Used in numeric type information for languages like COBOL and Fortran.
    """
    unsigned = 0x01
    leading_overpunch = 0x02
    trailing_overpunch = 0x03
    leading_separate = 0x04
    trailing_separate = 0x05


class Endianity(EnumBase):
    """DWARF Endianness Encodings.
    
    Defines DW_END_* constants that specify the endianness (byte order) of data types.
    Controls how multi-byte values are interpreted in memory.
    
    Attributes:
        default (0x00): Use default machine endianness.
        big (0x01): Big-endian byte order.
        little (0x02): Little-endian byte order.
    """
    default = 0x00
    big = 0x01
    little = 0x02
    lo_user = 0x40
    hi_user = 0xFF


class Accessibility(EnumBase):
    """DWARF Member Accessibility Encodings.
    
    Defines DW_ACCESS_* constants that specify the accessibility level of class/structure
    members (e.g., public, protected, private).
    
    Attributes:
        public (0x01): Public member, accessible to all.
        protected (0x02): Protected member, accessible to derived classes.
        private (0x03): Private member, accessible only within the class.
    """
    public = 0x01
    protected = 0x02
    private = 0x03


class Visibility(EnumBase):
    """DWARF Symbol Visibility Encodings.
    
    Defines DW_VIS_* constants that control the scope and visibility of symbols.
    Determines whether a symbol is visible across translation units.
    
    Attributes:
        local (0x01): Local visibility, restricted scope.
        exported (0x02): Exported visibility, visible externally.
        qualified (0x03): Qualified visibility.
    """
    local = 0x01
    exported = 0x02
    qualified = 0x03


class Virtuality(EnumBase):
    """DWARF Member Function Virtuality Encodings.
    
    Defines DW_VIRTUALITY_* constants that specify whether a member function
    is virtual, pure virtual, or non-virtual.
    
    Attributes:
        none (0x00): Non-virtual function.
        virtual (0x01): Virtual function, can be overridden.
        pure_virtual (0x02): Pure virtual function, must be overridden.
    """
    none = 0x00
    virtual = 0x01
    pure_virtual = 0x02


class IdentifierCase(EnumBase):
    case_sensitive = 0x00
    up_case = 0x01
    down_case = 0x02
    case_insensitive = 0x03


class CallingConvention(EnumBase):
    """DWARF Function Calling Convention Encodings.
    
    Defines DW_CC_* constants that specify the calling convention used by functions.
    Determines how arguments are passed, return values handled, and stack cleanup.
    
    Includes standard conventions (normal, program) and architecture-specific conventions
    (Renesas SH, Borland fastcall, Intel thiscall, etc.).
    
    Attributes:
        normal (0x01): Standard calling convention.
        program (0x02): Program calling convention.
        nocall (0x03): No call convention.
    """
    normal = 0x01
    program = 0x02
    nocall = 0x03
    renesas_sh = 0x40
    borland_fastcall_i386 = 0x41
    thiscall_i386 = 0x42
    lo_user = 0x60
    hi_user = 0xFF


class Inline(EnumBase):
    """DWARF Function Inlining Encodings.
    
    Defines DW_INL_* constants that control whether a function is inlined by the compiler.
    Describes the inlining status of a subprogram.
    
    Attributes:
        not_inlined (0x00): Function is not inlined.
        inlined (0x01): Function has been inlined.
        declared_not_inlined (0x02): Function declared as not to be inlined.
        declared_inlined (0x03): Function declared to be inlined.
    """
    not_inlined = 0x00
    inlined = 0x01
    declared_not_inlined = 0x02
    declared_inlined = 0x03


class Ordering(EnumBase):
    """DWARF Array Ordering Encodings.
    
    Defines DW_ORD_* constants that specify the storage order of array dimensions.
    Determines whether arrays are stored in row-major or column-major order.
    
    Attributes:
        row_major (0x00): Row-major array layout (C-style).
        col_major (0x01): Column-major array layout (Fortran-style).
    """
    row_major = 0x00
    col_major = 0x01


class DiscriminantDescriptor(EnumBase):
    """DWARF Discriminant Descriptor Encodings.
    
    Defines DW_DSC_* constants that describe how discriminant values are specified
    in variant type records (typically for Ada types).
    """
    label = 0x00
    range = 0x01


class Defaulted(EnumBase):
    """DWARF Defaulted Function Encodings.
    
    Defines DW_DEFAULTED_* constants that specify whether C++ member functions are
    explicitly or implicitly defaulted.
    
    Attributes:
        no (0x00): Function is user-provided or deleted.
        in_class (0x01): Function is defaulted inside the class definition.
        out_of_class (0x02): Function is defaulted outside the class definition.
    """
    no = 0x00
    in_class = 0x01
    out_of_class = 0x02


class LineNumberStandard(EnumBase):
    """DWARF Line Number Program Standard Opcodes.
    
    Defines DW_LNS_* constants for standard opcodes in the line number program.
    These opcodes control the state machine that generates line number information.
    
    Standard opcodes execute unconditionally and are followed by operands as needed.
    """
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
    """DWARF Line Number Program Extended Opcodes.
    
    Defines DW_LNE_* constants for extended opcodes in the line number program.
    Extended opcodes are identified by opcode value 0 followed by a length and opcode.
    
    Attributes:
        DW_LNE_end_sequence (0x01): End of line number sequence.
        DW_LNE_set_address (0x02): Set program counter address.
        DW_LNE_define_file (0x03): Define source file entry.
        DW_LNE_set_discriminator (0x04): Set discriminator value.
    """
    DW_LNE_end_sequence = 0x01
    DW_LNE_set_address = 0x02
    DW_LNE_define_file = 0x03
    DW_LNE_set_discriminator = 0x04
    DW_LNE_lo_user = 0x80
    DW_LNE_hi_user = 0xFF


class MacroInformation(EnumBase):
    """DWARF Macro Information Encodings.
    
    Defines DW_MACINFO_* constants that describe macro definition and inclusion
    entries in the .debug_macinfo section (DWARF4) or .debug_macro section (DWARF5).
    """
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
    """DWARF Exception Header Encoding (EH Frame).
    
    Defines DW_EH_PE_* constants used in the .eh_frame and .eh_frame_hdr sections
    to describe exception handling data representation. Linux-specific per LSB standard.
    
    Encodes both the encoding type (absolute, relative, etc.) and size format.
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
    """DWARF Call Frame Information Extensions.
    
    Defines DW_CFA_* constants for GNU-specific call frame information operations.
    Used in .debug_frame and .eh_frame sections for unwinding information.
    """
    DW_CFA_GNU_args_size = 0x2E
    DW_CFA_GNU_negative_offset_extended = 0x2F


class Languages(EnumBase):
    """DWARF Source Language Encodings.
    
    Defines DW_LANG_* constants that identify the source language of compiled code.
    Enables debuggers to apply language-specific formatting and semantics.
    
    Includes standard languages (C, C++, Fortran, Ada, etc.) and modern languages
    (Rust, Go, Swift, etc.) along with vendor-specific language extensions.
    """
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
