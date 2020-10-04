#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <github.com/Christoph2,
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

import enum

class Base(object):

    def __init__(self, value):
        self._value = value

    def _getValue(self):
        return self._value

    def __str__(self):
        return "< {0!s} >".format((self.MAP.get(self._value, self._value)))

    __repr__ = __str__

    value = property(_getValue)

##
## Tag encodings
##
DW_TAG_array_type               = 0x01
DW_TAG_class_type               = 0x02
DW_TAG_entry_point              = 0x03
DW_TAG_enumeration_type         = 0x04
DW_TAG_formal_parameter         = 0x05
DW_TAG_imported_declaration     = 0x08
DW_TAG_label                    = 0x0a
DW_TAG_lexical_block            = 0x0b
DW_TAG_member                   = 0x0d
DW_TAG_pointer_type             = 0x0f
DW_TAG_reference_type           = 0x10
DW_TAG_compile_unit             = 0x11
DW_TAG_string_type              = 0x12
DW_TAG_structure_type           = 0x13
DW_TAG_subroutine_type          = 0x15
DW_TAG_typedef                  = 0x16
DW_TAG_union_type               = 0x17
DW_TAG_unspecified_parameters   = 0x18
DW_TAG_variant                  = 0x19
DW_TAG_common_block             = 0x1a
DW_TAG_common_inclusion         = 0x1b
DW_TAG_inheritance              = 0x1c
DW_TAG_inlined_subroutine       = 0x1d
DW_TAG_module                   = 0x1e
DW_TAG_ptr_to_member_type       = 0x1f
DW_TAG_set_type                 = 0x20
DW_TAG_subrange_type            = 0x21
DW_TAG_with_stmt                = 0x22
DW_TAG_access_declaration       = 0x23
DW_TAG_base_type                = 0x24
DW_TAG_catch_block              = 0x25
DW_TAG_const_type               = 0x26
DW_TAG_constant                 = 0x27
DW_TAG_enumerator               = 0x28
DW_TAG_file_type                = 0x29
DW_TAG_friend                   = 0x2a
DW_TAG_namelist                 = 0x2b
DW_TAG_namelist_item            = 0x2c
DW_TAG_packed_type              = 0x2d
DW_TAG_subprogram               = 0x2e
DW_TAG_template_type_parameter  = 0x2f
DW_TAG_template_value_parameter = 0x30
DW_TAG_thrown_type              = 0x31
DW_TAG_try_block                = 0x32
DW_TAG_variant_part             = 0x33
DW_TAG_variable                 = 0x34
DW_TAG_volatile_type            = 0x35
DW_TAG_dwarf_procedure          = 0x36
DW_TAG_restrict_type            = 0x37
DW_TAG_interface_type           = 0x38
DW_TAG_namespace                = 0x39
DW_TAG_imported_module          = 0x3a
DW_TAG_unspecified_type         = 0x3b
DW_TAG_partial_unit             = 0x3c
DW_TAG_imported_unit            = 0x3d
DW_TAG_condition                = 0x3f
DW_TAG_shared_type              = 0x40
DW_TAG_type_unit                = 0x41
DW_TAG_rvalue_reference_type    = 0x42
DW_TAG_template_alias           = 0x43
DW_TAG_lo_user                  = 0x4080
DW_TAG_hi_user                  = 0xffff

TAG_MAP = {
    DW_TAG_array_type               : "DW_TAG_array_type",
    DW_TAG_class_type               : "DW_TAG_class_type",
    DW_TAG_entry_point              : "DW_TAG_entry_point",
    DW_TAG_enumeration_type         : "DW_TAG_enumeration_type",
    DW_TAG_formal_parameter         : "DW_TAG_formal_parameter",
    DW_TAG_imported_declaration     : "DW_TAG_imported_declaration",
    DW_TAG_label                    : "DW_TAG_label",
    DW_TAG_lexical_block            : "DW_TAG_lexical_block",
    DW_TAG_member                   : "DW_TAG_member",
    DW_TAG_pointer_type             : "DW_TAG_pointer_type",
    DW_TAG_reference_type           : "DW_TAG_reference_type",
    DW_TAG_compile_unit             : "DW_TAG_compile_unit",
    DW_TAG_string_type              : "DW_TAG_string_type",
    DW_TAG_structure_type           : "DW_TAG_structure_type",
    DW_TAG_subroutine_type          : "DW_TAG_subroutine_type",
    DW_TAG_typedef                  : "DW_TAG_typedef",
    DW_TAG_union_type               : "DW_TAG_union_type",
    DW_TAG_unspecified_parameters   : "DW_TAG_unspecified_parameters",
    DW_TAG_variant                  : "DW_TAG_variant",
    DW_TAG_common_block             : "DW_TAG_common_block",
    DW_TAG_common_inclusion         : "DW_TAG_common_inclusion",
    DW_TAG_inheritance              : "DW_TAG_inheritance",
    DW_TAG_inlined_subroutine       : "DW_TAG_inlined_subroutine",
    DW_TAG_module                   : "DW_TAG_module",
    DW_TAG_ptr_to_member_type       : "DW_TAG_ptr_to_member_type",
    DW_TAG_set_type                 : "DW_TAG_set_type",
    DW_TAG_subrange_type            : "DW_TAG_subrange_type",
    DW_TAG_with_stmt                : "DW_TAG_with_stmt",
    DW_TAG_access_declaration       : "DW_TAG_access_declaration",
    DW_TAG_base_type                : "DW_TAG_base_type",
    DW_TAG_catch_block              : "DW_TAG_catch_block",
    DW_TAG_const_type               : "DW_TAG_const_type",
    DW_TAG_constant                 : "DW_TAG_constant",
    DW_TAG_enumerator               : "DW_TAG_enumerator",
    DW_TAG_file_type                : "DW_TAG_file_type",
    DW_TAG_friend                   : "DW_TAG_friend",
    DW_TAG_namelist                 : "DW_TAG_namelist",
    DW_TAG_namelist_item            : "DW_TAG_namelist_item",
    DW_TAG_packed_type              : "DW_TAG_packed_type",
    DW_TAG_subprogram               : "DW_TAG_subprogram",
    DW_TAG_template_type_parameter  : "DW_TAG_template_type_parameter",
    DW_TAG_template_value_parameter : "DW_TAG_template_value_parameter",
    DW_TAG_thrown_type              : "DW_TAG_thrown_type",
    DW_TAG_try_block                : "DW_TAG_thrown_type",
    DW_TAG_variant_part             : "DW_TAG_variant_part",
    DW_TAG_variable                 : "DW_TAG_variable",
    DW_TAG_volatile_type            : "DW_TAG_volatile_type",
    DW_TAG_dwarf_procedure          : "DW_TAG_dwarf_procedure",
    DW_TAG_restrict_type            : "DW_TAG_restrict_type",
    DW_TAG_interface_type           : "DW_TAG_interface_type",
    DW_TAG_namespace                : "DW_TAG_namespace",
    DW_TAG_imported_module          : "DW_TAG_imported_module",
    DW_TAG_unspecified_type         : "DW_TAG_unspecified_type",
    DW_TAG_partial_unit             : "DW_TAG_partial_unit",
    DW_TAG_imported_unit            : "DW_TAG_imported_unit",
    DW_TAG_condition                : "DW_TAG_condition",
    DW_TAG_shared_type              : "DW_TAG_shared_type",
    DW_TAG_type_unit                : "DW_TAG_type_unit",
    DW_TAG_rvalue_reference_type    : "DW_TAG_rvalue_reference_type",
    DW_TAG_template_alias           : "DW_TAG_template_alias",
    DW_TAG_lo_user                  : "DW_TAG_lo_user",
    DW_TAG_hi_user                  : "DW_TAG_hi_user",
}

class Tag(Base):
    MAP = TAG_MAP

##
## Child determination encodings.
##
DW_CHILDREN_no                  = 0x00
DW_CHILDREN_yes                 = 0x01

CHILDREN_MAP = {
    DW_CHILDREN_no              : "DW_CHILDREN_no",
    DW_CHILDREN_yes             : "DW_CHILDREN_yes",
}

class Children(Base):
    MAP = CHILDREN_MAP

##
## Attribute encodings.
##
DW_AT_sibling                   = 0x01
DW_AT_location                  = 0x02
DW_AT_name                      = 0x03
DW_AT_ordering                  = 0x09
DW_AT_byte_size                 = 0x0b
DW_AT_bit_offset                = 0x0c
DW_AT_bit_size                  = 0x0d
DW_AT_stmt_list                 = 0x10
DW_AT_low_pc                    = 0x11
DW_AT_high_pc                   = 0x12
DW_AT_language                  = 0x13
DW_AT_discr                     = 0x15
DW_AT_discr_value               = 0x16
DW_AT_visibility                = 0x17
DW_AT_import                    = 0x18
DW_AT_string_length             = 0x19
DW_AT_common_reference          = 0x1a
DW_AT_comp_dir                  = 0x1b
DW_AT_const_value               = 0x1c
DW_AT_containing_type           = 0x1d
DW_AT_default_value             = 0x1e
DW_AT_inline                    = 0x20
DW_AT_is_optional               = 0x21
DW_AT_lower_bound               = 0x22
DW_AT_producer                  = 0x25
DW_AT_prototyped                = 0x27
DW_AT_return_addr               = 0x2a
DW_AT_start_scope               = 0x2c
DW_AT_bit_stride                = 0x2e
DW_AT_upper_bound               = 0x2f
DW_AT_abstract_origin           = 0x31
DW_AT_accessibility             = 0x32
DW_AT_address_class             = 0x33
DW_AT_artificial                = 0x34
DW_AT_base_types                = 0x35
DW_AT_calling_convention        = 0x36
DW_AT_count                     = 0x37
DW_AT_data_member_location      = 0x38
DW_AT_decl_column               = 0x39
DW_AT_decl_file                 = 0x3a
DW_AT_decl_line                 = 0x3b
DW_AT_declaration               = 0x3c
DW_AT_discr_list                = 0x3d
DW_AT_encoding                  = 0x3e
DW_AT_external                  = 0x3f
DW_AT_frame_base                = 0x40
DW_AT_friend                    = 0x41
DW_AT_identifier_case           = 0x42
DW_AT_macro_info                = 0x43
DW_AT_namelist_item             = 0x44
DW_AT_priority                  = 0x45
DW_AT_segment                   = 0x46
DW_AT_specification             = 0x47
DW_AT_static_link               = 0x48
DW_AT_type                      = 0x49
DW_AT_use_location              = 0x4a
DW_AT_variable_parameter        = 0x4b
DW_AT_virtuality                = 0x4c
DW_AT_vtable_elem_location      = 0x4d
DW_AT_allocated                 = 0x4e
DW_AT_associated                = 0x4f
DW_AT_data_location             = 0x50
DW_AT_byte_stride               = 0x51
DW_AT_entry_pc                  = 0x52
DW_AT_use_UTF8                  = 0x53
DW_AT_extension                 = 0x54
DW_AT_ranges                    = 0x55
DW_AT_trampoline                = 0x56
DW_AT_call_column               = 0x57
DW_AT_call_file                 = 0x58
DW_AT_call_line                 = 0x59
DW_AT_description               = 0x5a
DW_AT_binary_scale              = 0x5b
DW_AT_decimal_scale             = 0x5c
DW_AT_small                     = 0x5d
DW_AT_decimal_sign              = 0x5e
DW_AT_digit_count               = 0x5f
DW_AT_picture_string            = 0x60
DW_AT_mutable                   = 0x61
DW_AT_threads_scaled            = 0x62
DW_AT_explicit                  = 0x63
DW_AT_object_pointer            = 0x64
DW_AT_endianity                 = 0x65
DW_AT_elemental                 = 0x66
DW_AT_pure                      = 0x67
DW_AT_recursive                 = 0x68
DW_AT_signature                 = 0x69
DW_AT_main_subprogram           = 0x6a
DW_AT_data_bit_offset           = 0x6b
DW_AT_const_expr                = 0x6c
DW_AT_enum_class                = 0x6d
DW_AT_linkage_name              = 0x6e
DW_AT_lo_user                   = 0x2000
DW_AT_hi_user                   = 0x3fff

ATTR_MAP = {
    DW_AT_sibling                   : "DW_AT_sibling",
    DW_AT_location                  : "DW_AT_location",
    DW_AT_name                      : "DW_AT_name",
    DW_AT_ordering                  : "DW_AT_ordering",
    DW_AT_byte_size                 : "DW_AT_byte_size",
    DW_AT_bit_offset                : "DW_AT_bit_offset",
    DW_AT_bit_size                  : "DW_AT_bit_size",
    DW_AT_stmt_list                 : "DW_AT_stmt_list",
    DW_AT_low_pc                    : "DW_AT_low_pc",
    DW_AT_high_pc                   : "DW_AT_high_pc",
    DW_AT_language                  : "DW_AT_language",
    DW_AT_discr                     : "DW_AT_discr",
    DW_AT_discr_value               : "DW_AT_discr_value",
    DW_AT_visibility                : "DW_AT_visibility",
    DW_AT_import                    : "DW_AT_import",
    DW_AT_string_length             : "DW_AT_string_length",
    DW_AT_common_reference          : "DW_AT_common_reference",
    DW_AT_comp_dir                  : "DW_AT_comp_dir",
    DW_AT_const_value               : "DW_AT_const_value",
    DW_AT_containing_type           : "DW_AT_containing_type",
    DW_AT_default_value             : "DW_AT_default_value",
    DW_AT_inline                    : "DW_AT_inline",
    DW_AT_is_optional               : "DW_AT_is_optional",
    DW_AT_lower_bound               : "DW_AT_lower_bound",
    DW_AT_producer                  : "DW_AT_producer",
    DW_AT_prototyped                : "DW_AT_prototyped",
    DW_AT_return_addr               : "DW_AT_return_addr",
    DW_AT_start_scope               : "DW_AT_start_scope",
    DW_AT_bit_stride                : "DW_AT_bit_stride",
    DW_AT_upper_bound               : "DW_AT_upper_bound",
    DW_AT_abstract_origin           : "DW_AT_abstract_origin",
    DW_AT_accessibility             : "DW_AT_accessibility",
    DW_AT_address_class             : "DW_AT_address_class",
    DW_AT_artificial                : "DW_AT_artificial",
    DW_AT_base_types                : "DW_AT_base_types",
    DW_AT_calling_convention        : "DW_AT_calling_convention",
    DW_AT_count                     : "DW_AT_count",
    DW_AT_data_member_location      : "DW_AT_data_member_location",
    DW_AT_decl_column               : "DW_AT_decl_column",
    DW_AT_decl_file                 : "DW_AT_decl_file",
    DW_AT_decl_line                 : "DW_AT_decl_line",
    DW_AT_declaration               : "DW_AT_declaration",
    DW_AT_discr_list                : "DW_AT_discr_list",
    DW_AT_encoding                  : "DW_AT_encoding",
    DW_AT_external                  : "DW_AT_external",
    DW_AT_frame_base                : "DW_AT_frame_base",
    DW_AT_friend                    : "DW_AT_friend",
    DW_AT_identifier_case           : "DW_AT_identifier_case",
    DW_AT_macro_info                : "DW_AT_macro_info",
    DW_AT_namelist_item             : "DW_AT_namelist_item",
    DW_AT_priority                  : "DW_AT_priority",
    DW_AT_segment                   : "DW_AT_segment",
    DW_AT_specification             : "DW_AT_specification",
    DW_AT_static_link               : "DW_AT_static_link",
    DW_AT_type                      : "DW_AT_type",
    DW_AT_use_location              : "DW_AT_use_location",
    DW_AT_variable_parameter        : "DW_AT_variable_parameter",
    DW_AT_virtuality                : "DW_AT_virtuality",
    DW_AT_vtable_elem_location      : "DW_AT_vtable_elem_location",
    DW_AT_allocated                 : "DW_AT_allocated",
    DW_AT_associated                : "DW_AT_associated",
    DW_AT_data_location             : "DW_AT_data_location",
    DW_AT_byte_stride               : "DW_AT_byte_stride",
    DW_AT_entry_pc                  : "DW_AT_entry_pc",
    DW_AT_use_UTF8                  : "DW_AT_use_UTF8",
    DW_AT_extension                 : "DW_AT_extension",
    DW_AT_ranges                    : "DW_AT_ranges",
    DW_AT_trampoline                : "DW_AT_trampoline",
    DW_AT_call_column               : "DW_AT_call_column",
    DW_AT_call_file                 : "DW_AT_call_file",
    DW_AT_call_line                 : "DW_AT_call_line",
    DW_AT_description               : "DW_AT_description",
    DW_AT_binary_scale              : "DW_AT_binary_scale",
    DW_AT_decimal_scale             : "DW_AT_decimal_scale",
    DW_AT_small                     : "DW_AT_small",
    DW_AT_decimal_sign              : "DW_AT_decimal_sign",
    DW_AT_digit_count               : "DW_AT_digit_count",
    DW_AT_picture_string            : "DW_AT_picture_string",
    DW_AT_mutable                   : "DW_AT_mutable",
    DW_AT_threads_scaled            : "DW_AT_threads_scaled",
    DW_AT_explicit                  : "DW_AT_explicit",
    DW_AT_object_pointer            : "DW_AT_object_pointer",
    DW_AT_endianity                 : "DW_AT_endianity",
    DW_AT_elemental                 : "DW_AT_elemental",
    DW_AT_pure                      : "DW_AT_pure",
    DW_AT_recursive                 : "DW_AT_recursive",
    DW_AT_signature                 : "DW_AT_signature",
    DW_AT_main_subprogram           : "DW_AT_main_subprogram",
    DW_AT_data_bit_offset           : "DW_AT_data_bit_offset",
    DW_AT_const_expr                : "DW_AT_const_expr",
    DW_AT_enum_class                : "DW_AT_enum_class",
    DW_AT_linkage_name              : "DW_AT_linkage_name",
    DW_AT_lo_user                   : "DW_AT_lo_user",
    DW_AT_hi_user                   : "DW_AT_hi_user",
}

class AttributeEncoding(Base):
    MAP = ATTR_MAP

'''
FORM_MAP = {
    DW_FORM_addr                : "DW_FORM_addr",
    DW_FORM_block2              : "DW_FORM_block2",
    DW_FORM_block4              : "DW_FORM_block4",
    DW_FORM_data2               : "DW_FORM_data2",
    DW_FORM_data4               : "DW_FORM_data4",
    DW_FORM_data8               : "DW_FORM_data8",
    DW_FORM_string              : "DW_FORM_string",
    DW_FORM_block               : "DW_FORM_block",
    DW_FORM_block1              : "DW_FORM_block1",
    DW_FORM_data1               : "DW_FORM_data1",
    DW_FORM_flag                : "DW_FORM_flag",
    DW_FORM_sdata               : "DW_FORM_sdata",
    DW_FORM_strp                : "DW_FORM_strp",
    DW_FORM_udata               : "DW_FORM_udata",
    DW_FORM_ref_addr            : "DW_FORM_ref_addr",
    DW_FORM_ref1                : "DW_FORM_ref1",
    DW_FORM_ref2                : "DW_FORM_ref2",
    DW_FORM_ref4                : "DW_FORM_ref4",
    DW_FORM_ref8                : "DW_FORM_ref8",
    DW_FORM_ref_udata           : "DW_FORM_ref_udata",
    DW_FORM_indirect            : "DW_FORM_indirect",
    DW_FORM_sec_offset          : "DW_FORM_sec_offset",
    DW_FORM_exprloc             : "DW_FORM_exprloc",
    DW_FORM_flag_present        : "DW_FORM_flag_present",
    DW_FORM_ref_sig8            : "DW_FORM_ref_sig8",
}
'''

class AttributeForm(enum.IntEnum):
    #MAP = FORM_MAP
    ##
    ## Attribute form encodings.
    ##
    DW_FORM_addr                    = 0x01
    DW_FORM_block2                  = 0x03
    DW_FORM_block4                  = 0x04
    DW_FORM_data2                   = 0x05
    DW_FORM_data4                   = 0x06
    DW_FORM_data8                   = 0x07
    DW_FORM_string                  = 0x08
    DW_FORM_block                   = 0x09
    DW_FORM_block1                  = 0x0a
    DW_FORM_data1                   = 0x0b
    DW_FORM_flag                    = 0x0c
    DW_FORM_sdata                   = 0x0d
    DW_FORM_strp                    = 0x0e
    DW_FORM_udata                   = 0x0f
    DW_FORM_ref_addr                = 0x10
    DW_FORM_ref1                    = 0x11
    DW_FORM_ref2                    = 0x12
    DW_FORM_ref4                    = 0x13
    DW_FORM_ref8                    = 0x14
    DW_FORM_ref_udata               = 0x15
    DW_FORM_indirect                = 0x16
    DW_FORM_sec_offset              = 0x17
    DW_FORM_exprloc                 = 0x18
    DW_FORM_flag_present            = 0x19
    DW_FORM_ref_sig8                = 0x20

##
## DWARF operation encodings.
##
DW_OP_addr                      = 0x03
DW_OP_deref                     = 0x06
DW_OP_const1u                   = 0x08
DW_OP_const1s                   = 0x09
DW_OP_const2u                   = 0x0a
DW_OP_const2s                   = 0x0b
DW_OP_const4u                   = 0x0c
DW_OP_const4s                   = 0x0d
DW_OP_const8u                   = 0x0e
DW_OP_const8s                   = 0x0f
DW_OP_constu                    = 0x10
DW_OP_consts                    = 0x11
DW_OP_dup                       = 0x12
DW_OP_drop                      = 0x13
DW_OP_over                      = 0x14
DW_OP_pick                      = 0x15
DW_OP_swap                      = 0x16
DW_OP_rot                       = 0x17
DW_OP_xderef                    = 0x18
DW_OP_abs                       = 0x19
DW_OP_and                       = 0x1a
DW_OP_div                       = 0x1b
DW_OP_minus                     = 0x1c
DW_OP_mod                       = 0x1d
DW_OP_mul                       = 0x1e
DW_OP_neg                       = 0x1f
DW_OP_not                       = 0x20
DW_OP_or                        = 0x21
DW_OP_plus                      = 0x22
DW_OP_plus_uconst               = 0x23
DW_OP_shl                       = 0x24
DW_OP_shr                       = 0x25
DW_OP_shra                      = 0x26
DW_OP_xor                       = 0x27
DW_OP_skip                      = 0x2f
DW_OP_bra                       = 0x28
DW_OP_eq                        = 0x29
DW_OP_ge                        = 0x2a
DW_OP_gt                        = 0x2b
DW_OP_le                        = 0x2c
DW_OP_lt                        = 0x2d
DW_OP_ne                        = 0x2e
DW_OP_lit0                      = 0x30
DW_OP_lit1                      = 0x31
DW_OP_lit2                      = 0x32
DW_OP_lit3                      = 0x33
DW_OP_lit4                      = 0x34
DW_OP_lit5                      = 0x35
DW_OP_lit6                      = 0x36
DW_OP_lit7                      = 0x37
DW_OP_lit8                      = 0x38
DW_OP_lit9                      = 0x39
DW_OP_lit10                     = 0x3a
DW_OP_lit11                     = 0x3b
DW_OP_lit12                     = 0x3c
DW_OP_lit13                     = 0x3d
DW_OP_lit14                     = 0x3e
DW_OP_lit15                     = 0x3f
DW_OP_lit16                     = 0x40
DW_OP_lit17                     = 0x41
DW_OP_lit18                     = 0x42
DW_OP_lit19                     = 0x43
DW_OP_lit20                     = 0x44
DW_OP_lit21                     = 0x45
DW_OP_lit22                     = 0x46
DW_OP_lit23                     = 0x47
DW_OP_lit24                     = 0x48
DW_OP_lit25                     = 0x49
DW_OP_lit26                     = 0x4a
DW_OP_lit27                     = 0x4b
DW_OP_lit28                     = 0x4c
DW_OP_lit29                     = 0x4d
DW_OP_lit30                     = 0x4e
DW_OP_lit31                     = 0x4f
DW_OP_reg0                      = 0x50
DW_OP_reg1                      = 0x51
DW_OP_reg2                      = 0x52
DW_OP_reg3                      = 0x53
DW_OP_reg4                      = 0x54
DW_OP_reg5                      = 0x55
DW_OP_reg6                      = 0x56
DW_OP_reg7                      = 0x57
DW_OP_reg8                      = 0x58
DW_OP_reg9                      = 0x59
DW_OP_reg10                     = 0x5a
DW_OP_reg11                     = 0x5b
DW_OP_reg12                     = 0x5c
DW_OP_reg13                     = 0x5d
DW_OP_reg14                     = 0x5e
DW_OP_reg15                     = 0x5f
DW_OP_reg16                     = 0x60
DW_OP_reg17                     = 0x61
DW_OP_reg18                     = 0x62
DW_OP_reg19                     = 0x63
DW_OP_reg20                     = 0x64
DW_OP_reg21                     = 0x65
DW_OP_reg22                     = 0x66
DW_OP_reg23                     = 0x67
DW_OP_reg24                     = 0x68
DW_OP_reg25                     = 0x69
DW_OP_reg26                     = 0x6a
DW_OP_reg27                     = 0x6b
DW_OP_reg28                     = 0x6c
DW_OP_reg29                     = 0x6d
DW_OP_reg30                     = 0x6e
DW_OP_reg31                     = 0x6f
DW_OP_breg0                     = 0x70
DW_OP_breg1                     = 0x71
DW_OP_breg2                     = 0x72
DW_OP_breg3                     = 0x73
DW_OP_breg4                     = 0x74
DW_OP_breg5                     = 0x75
DW_OP_breg6                     = 0x76
DW_OP_breg7                     = 0x77
DW_OP_breg8                     = 0x78
DW_OP_breg9                     = 0x79
DW_OP_breg10                    = 0x7a
DW_OP_breg11                    = 0x7b
DW_OP_breg12                    = 0x7c
DW_OP_breg13                    = 0x7d
DW_OP_breg14                    = 0x7e
DW_OP_breg15                    = 0x7f
DW_OP_breg16                    = 0x80
DW_OP_breg17                    = 0x81
DW_OP_breg18                    = 0x82
DW_OP_breg19                    = 0x83
DW_OP_breg20                    = 0x84
DW_OP_breg21                    = 0x85
DW_OP_breg22                    = 0x86
DW_OP_breg23                    = 0x87
DW_OP_breg24                    = 0x88
DW_OP_breg25                    = 0x89
DW_OP_breg26                    = 0x8a
DW_OP_breg27                    = 0x8b
DW_OP_breg28                    = 0x8c
DW_OP_breg29                    = 0x8d
DW_OP_breg30                    = 0x8e
DW_OP_breg31                    = 0x8f
DW_OP_regx                      = 0x90
DW_OP_fbreg                     = 0x91
DW_OP_bregx                     = 0x92
DW_OP_piece                     = 0x93
DW_OP_deref_size                = 0x94
DW_OP_xderef_size               = 0x95
DW_OP_nop                       = 0x96
DW_OP_push_object_address       = 0x97
DW_OP_call2                     = 0x98
DW_OP_call4                     = 0x99
DW_OP_call_ref                  = 0x9a
DW_OP_form_tls_address          = 0x9b
DW_OP_call_frame_cfa            = 0x9c
DW_OP_bit_piece                 = 0x9d
DW_OP_implicit_value            = 0x9e
DW_OP_stack_value               = 0x9f
DW_OP_lo_user                   = 0xe0
DW_OP_hi_user                   = 0xff

OPERATION_MAP = {
    DW_OP_addr                  : "DW_OP_addr",
    DW_OP_deref                 : "DW_OP_deref",
    DW_OP_const1u               : "DW_OP_const1u",
    DW_OP_const1s               : "DW_OP_const1s",
    DW_OP_const2u               : "DW_OP_const2u",
    DW_OP_const2s               : "DW_OP_const2s",
    DW_OP_const4u               : "DW_OP_const4u",
    DW_OP_const4s               : "DW_OP_const4s",
    DW_OP_const8u               : "DW_OP_const8u",
    DW_OP_const8s               : "DW_OP_const8s",
    DW_OP_constu                : "DW_OP_constu",
    DW_OP_consts                : "DW_OP_consts",
    DW_OP_dup                   : "DW_OP_dup",
    DW_OP_drop                  : "DW_OP_drop",
    DW_OP_over                  : "DW_OP_over",
    DW_OP_pick                  : "DW_OP_pick",
    DW_OP_swap                  : "DW_OP_swap",
    DW_OP_rot                   : "DW_OP_rot",
    DW_OP_xderef                : "DW_OP_xderef",
    DW_OP_abs                   : "DW_OP_abs",
    DW_OP_and                   : "DW_OP_and",
    DW_OP_div                   : "DW_OP_div",
    DW_OP_minus                 : "DW_OP_minus",
    DW_OP_mod                   : "DW_OP_mod",
    DW_OP_mul                   : "DW_OP_mul",
    DW_OP_neg                   : "DW_OP_neg",
    DW_OP_not                   : "DW_OP_not",
    DW_OP_or                    : "DW_OP_or",
    DW_OP_plus                  : "DW_OP_plus",
    DW_OP_plus_uconst           : "DW_OP_plus_uconst",
    DW_OP_shl                   : "DW_OP_shl",
    DW_OP_shr                   : "DW_OP_shr",
    DW_OP_shra                  : "DW_OP_shra",
    DW_OP_xor                   : "DW_OP_xor",
    DW_OP_skip                  : "DW_OP_skip",
    DW_OP_bra                   : "DW_OP_bra",
    DW_OP_eq                    : "DW_OP_eq",
    DW_OP_ge                    : "DW_OP_ge",
    DW_OP_gt                    : "DW_OP_gt",
    DW_OP_le                    : "DW_OP_le",
    DW_OP_lt                    : "DW_OP_lt",
    DW_OP_ne                    : "DW_OP_ne",
    DW_OP_lit0                  : "DW_OP_lit0",
    DW_OP_lit1                  : "DW_OP_lit1",
    DW_OP_lit2                  : "DW_OP_lit2",
    DW_OP_lit3                  : "DW_OP_lit3",
    DW_OP_lit4                  : "DW_OP_lit4",
    DW_OP_lit5                  : "DW_OP_lit5",
    DW_OP_lit6                  : "DW_OP_lit6",
    DW_OP_lit7                  : "DW_OP_lit7",
    DW_OP_lit8                  : "DW_OP_lit8",
    DW_OP_lit9                  : "DW_OP_lit9",
    DW_OP_lit10                 : "DW_OP_lit10",
    DW_OP_lit11                 : "DW_OP_lit11",
    DW_OP_lit12                 : "DW_OP_lit12",
    DW_OP_lit13                 : "DW_OP_lit13",
    DW_OP_lit14                 : "DW_OP_lit14",
    DW_OP_lit15                 : "DW_OP_lit15",
    DW_OP_lit16                 : "DW_OP_lit16",
    DW_OP_lit17                 : "DW_OP_lit17",
    DW_OP_lit18                 : "DW_OP_lit18",
    DW_OP_lit19                 : "DW_OP_lit19",
    DW_OP_lit20                 : "DW_OP_lit20",
    DW_OP_lit21                 : "DW_OP_lit21",
    DW_OP_lit22                 : "DW_OP_lit22",
    DW_OP_lit23                 : "DW_OP_lit23",
    DW_OP_lit24                 : "DW_OP_lit24",
    DW_OP_lit25                 : "DW_OP_lit25",
    DW_OP_lit26                 : "DW_OP_lit26",
    DW_OP_lit27                 : "DW_OP_lit27",
    DW_OP_lit28                 : "DW_OP_lit28",
    DW_OP_lit29                 : "DW_OP_lit29",
    DW_OP_lit30                 : "DW_OP_lit30",
    DW_OP_lit31                 : "DW_OP_lit31",
    DW_OP_reg0                  : "DW_OP_reg0",
    DW_OP_reg1                  : "DW_OP_reg1",
    DW_OP_reg2                  : "DW_OP_reg2",
    DW_OP_reg3                  : "DW_OP_reg3",
    DW_OP_reg4                  : "DW_OP_reg4",
    DW_OP_reg5                  : "DW_OP_reg5",
    DW_OP_reg6                  : "DW_OP_reg6",
    DW_OP_reg7                  : "DW_OP_reg7",
    DW_OP_reg8                  : "DW_OP_reg8",
    DW_OP_reg9                  : "DW_OP_reg9",
    DW_OP_reg10                 : "DW_OP_reg10",
    DW_OP_reg11                 : "DW_OP_reg11",
    DW_OP_reg12                 : "DW_OP_reg12",
    DW_OP_reg13                 : "DW_OP_reg13",
    DW_OP_reg14                 : "DW_OP_reg14",
    DW_OP_reg15                 : "DW_OP_reg15",
    DW_OP_reg16                 : "DW_OP_reg16",
    DW_OP_reg17                 : "DW_OP_reg17",
    DW_OP_reg18                 : "DW_OP_reg18",
    DW_OP_reg19                 : "DW_OP_reg19",
    DW_OP_reg20                 : "DW_OP_reg20",
    DW_OP_reg21                 : "DW_OP_reg21",
    DW_OP_reg22                 : "DW_OP_reg22",
    DW_OP_reg23                 : "DW_OP_reg23",
    DW_OP_reg24                 : "DW_OP_reg24",
    DW_OP_reg25                 : "DW_OP_reg25",
    DW_OP_reg26                 : "DW_OP_reg26",
    DW_OP_reg27                 : "DW_OP_reg27",
    DW_OP_reg28                 : "DW_OP_reg28",
    DW_OP_reg29                 : "DW_OP_reg29",
    DW_OP_reg30                 : "DW_OP_reg30",
    DW_OP_reg31                 : "DW_OP_reg31",
    DW_OP_breg0                 : "DW_OP_breg0",
    DW_OP_breg1                 : "DW_OP_breg1",
    DW_OP_breg2                 : "DW_OP_breg2",
    DW_OP_breg3                 : "DW_OP_breg3",
    DW_OP_breg4                 : "DW_OP_breg4",
    DW_OP_breg5                 : "DW_OP_breg5",
    DW_OP_breg6                 : "DW_OP_breg6",
    DW_OP_breg7                 : "DW_OP_breg7",
    DW_OP_breg8                 : "DW_OP_breg8",
    DW_OP_breg9                 : "DW_OP_breg9",
    DW_OP_breg10                : "DW_OP_breg10",
    DW_OP_breg11                : "DW_OP_breg11",
    DW_OP_breg12                : "DW_OP_breg12",
    DW_OP_breg13                : "DW_OP_breg13",
    DW_OP_breg14                : "DW_OP_breg14",
    DW_OP_breg15                : "DW_OP_breg15",
    DW_OP_breg16                : "DW_OP_breg16",
    DW_OP_breg17                : "DW_OP_breg17",
    DW_OP_breg18                : "DW_OP_breg18",
    DW_OP_breg19                : "DW_OP_breg19",
    DW_OP_breg20                : "DW_OP_breg20",
    DW_OP_breg21                : "DW_OP_breg21",
    DW_OP_breg22                : "DW_OP_breg22",
    DW_OP_breg23                : "DW_OP_breg23",
    DW_OP_breg24                : "DW_OP_breg24",
    DW_OP_breg25                : "DW_OP_breg25",
    DW_OP_breg26                : "DW_OP_breg26",
    DW_OP_breg27                : "DW_OP_breg27",
    DW_OP_breg28                : "DW_OP_breg28",
    DW_OP_breg28                : "DW_OP_breg28",
    DW_OP_breg30                : "DW_OP_breg30",
    DW_OP_breg31                : "DW_OP_breg31",
    DW_OP_regx                  : "DW_OP_regx",
    DW_OP_fbreg                 : "DW_OP_fbreg",
    DW_OP_bregx                 : "DW_OP_bregx",
    DW_OP_piece                 : "DW_OP_piece",
    DW_OP_deref_size            : "DW_OP_deref_size",
    DW_OP_xderef_size           : "DW_OP_xderef_size",
    DW_OP_nop                   : "DW_OP_nop",
    DW_OP_push_object_address   : "DW_OP_push_object_address",
    DW_OP_call2                 : "DW_OP_call2",
    DW_OP_call4                 : "DW_OP_call4",
    DW_OP_call_ref              : "DW_OP_call_ref",
    DW_OP_form_tls_address      : "DW_OP_form_tls_address",
    DW_OP_call_frame_cfa        : "DW_OP_call_frame_cfa",
    DW_OP_bit_piece             : "DW_OP_bit_piece",
    DW_OP_implicit_value        : "DW_OP_implicit_value",
    DW_OP_stack_value           : "DW_OP_stack_value",
    DW_OP_lo_user               : "DW_OP_lo_user",
    DW_OP_hi_user               : "DW_OP_hi_user",
}

class Operation(Base):
    MAP = OPERATION_MAP


##
## Base type encoding values.
##
DW_ATE_address                  = 0x01
DW_ATE_boolean                  = 0x02
DW_ATE_complex_float            = 0x03
DW_ATE_float                    = 0x04
DW_ATE_signed                   = 0x05
DW_ATE_signed_char              = 0x06
DW_ATE_unsigned                 = 0x07
DW_ATE_unsigned_char            = 0x08
DW_ATE_imaginary_float          = 0x09
DW_ATE_packed_decimal           = 0x0a
DW_ATE_numeric_string           = 0x0b
DW_ATE_edited                   = 0x0c
DW_ATE_signed_fixed             = 0x0d
DW_ATE_unsigned_fixed           = 0x0e
DW_ATE_decimal_float            = 0x0f
DW_ATE_UTF                      = 0x10
DW_ATE_lo_user                  = 0x80
DW_ATE_hi_user                  = 0xff

ATE_MAP = {
    DW_ATE_address              : "DW_ATE_address",
    DW_ATE_boolean              : "DW_ATE_boolean",
    DW_ATE_complex_float        : "DW_ATE_complex_float",
    DW_ATE_float                : "DW_ATE_float",
    DW_ATE_signed               : "DW_ATE_signed",
    DW_ATE_signed_char          : "DW_ATE_signed_char",
    DW_ATE_unsigned             : "DW_ATE_unsigned",
    DW_ATE_unsigned_char        : "DW_ATE_unsigned_char",
    DW_ATE_imaginary_float      : "DW_ATE_imaginary_float",
    DW_ATE_packed_decimal       : "DW_ATE_packed_decimal",
    DW_ATE_numeric_string       : "DW_ATE_numeric_string",
    DW_ATE_edited               : "DW_ATE_edited",
    DW_ATE_signed_fixed         : "DW_ATE_signed_fixed",
    DW_ATE_unsigned_fixed       : "DW_ATE_unsigned_fixed",
    DW_ATE_decimal_float        : "DW_ATE_decimal_float",
    DW_ATE_UTF                  : "DW_ATE_UTF",
    DW_ATE_lo_user              : "DW_ATE_lo_user",
    DW_ATE_hi_user              : "DW_ATE_hi_user",
}

class BaseTypeEncoding(Base):
    MAP = ATE_MAP


##
## Decimal sign encodings.
##
DW_DS_unsigned                  = 0x01
DW_DS_leading_overpunch         = 0x02
DW_DS_trailing_overpunch        = 0x03
DW_DS_leading_separate          = 0x04
DW_DS_trailing_separate         = 0x05

DS_MAP = {
    DW_DS_unsigned              : "DW_DS_unsigned",
    DW_DS_leading_overpunch     : "DW_DS_leading_overpunch",
    DW_DS_trailing_overpunch    : "DW_DS_trailing_overpunch",
    DW_DS_leading_separate      : "DW_DS_leading_separate",
    DW_DS_trailing_separate     : "DW_DS_trailing_separate",
}

class DecimalSign(Base):
    MAP = DS_MAP

##
## Endianity encoding.
##
DW_END_default                  = 0x00
DW_END_big                      = 0x01
DW_END_little                   = 0x02
DW_END_lo_user                  = 0x40
DW_END_hi_user                  = 0xff

END_MAP = {
    DW_END_default              : "DW_END_default",
    DW_END_big                  : "DW_END_big",
    DW_END_little               : "DW_END_little",
    DW_END_lo_user              : "DW_END_lo_user",
    DW_END_hi_user              : "DW_END_hi_user",
}

class Endianity(Base):
    MAP = END_MAP

##
## Accessibility encodings.
##
DW_ACCESS_public                = 0x01
DW_ACCESS_protected             = 0x02
DW_ACCESS_private               = 0x03

ACCESS_MAP = {
    DW_ACCESS_public            : "DW_ACCESS_public",
    DW_ACCESS_protected         : "DW_ACCESS_protected",
    DW_ACCESS_private           : "DW_ACCESS_private",
}

class Accessibility(Base):
    MAP = ACCESS_MAP

##
## Visibility encodings.
##
DW_VIS_local                    = 0x01
DW_VIS_exported                 = 0x02
DW_VIS_qualified                = 0x03

VIS_MAP = {
    DW_VIS_local                : "DW_VIS_local",
    DW_VIS_exported             : "DW_VIS_exported",
    DW_VIS_qualified            : "DW_VIS_qualified",
}

class Visibility(Base):
    MAP = VIS_MAP

##
## Virtuality encodings.
##
DW_VIRTUALITY_none              = 0x00
DW_VIRTUALITY_virtual           = 0x01
DW_VIRTUALITY_pure_virtual      = 0x02

VIRTUALITY_MAP = {
    DW_VIRTUALITY_none          : "DW_VIRTUALITY_none",
    DW_VIRTUALITY_virtual       : "DW_VIRTUALITY_virtual",
    DW_VIRTUALITY_pure_virtual  : "DW_VIRTUALITY_pure_virtual",
}

class Virtuality(Base):
    MAP = VIRTUALITY_MAP


##
## Language encodings.
##
DW_LANG_C89                     = 0x0001    # 0
DW_LANG_C                       = 0x0002    # 0
DW_LANG_Ada83                   = 0x0003    # 1
DW_LANG_C_plus_plus             = 0x0004    # 0
DW_LANG_Cobol74                 = 0x0005    # 1
DW_LANG_Cobol85                 = 0x0006    # 1
DW_LANG_Fortran77               = 0x0007    # 1
DW_LANG_Fortran90               = 0x0008    # 1
DW_LANG_Pascal83                = 0x0009    # 1
DW_LANG_Modula2                 = 0x000a    # 1
DW_LANG_Java                    = 0x000b    # 0
DW_LANG_C99                     = 0x000c    # 0
DW_LANG_Ada95                   = 0x000d    # 1
DW_LANG_Fortran95               = 0x000e    # 1
DW_LANG_PLI                     = 0x000f    # 1
DW_LANG_ObjC                    = 0x0010    # 0
DW_LANG_ObjC_plus_plus          = 0x0011    # 0
DW_LANG_UPC                     = 0x0012    # 0
DW_LANG_D                       = 0x0013    # 0
DW_LANG_Python                  = 0x0014    # 0
DW_LANG_lo_user                 = 0x8000
DW_LANG_hi_user                 = 0xffff

LANG_MAP = {
    DW_LANG_C89                 : "DW_LANG_C89",
    DW_LANG_C                   : "DW_LANG_C",
    DW_LANG_Ada83               : "DW_LANG_Ada83",
    DW_LANG_C_plus_plus         : "DW_LANG_C_plus_plus",
    DW_LANG_Cobol74             : "DW_LANG_Cobol74",
    DW_LANG_Cobol85             : "DW_LANG_Cobol85",
    DW_LANG_Fortran77           : "DW_LANG_Fortran77",
    DW_LANG_Fortran90           : "DW_LANG_Fortran90",
    DW_LANG_Pascal83            : "DW_LANG_Pascal83",
    DW_LANG_Modula2             : "DW_LANG_Modula2",
    DW_LANG_Java                : "DW_LANG_Java",
    DW_LANG_C99                 : "DW_LANG_C99",
    DW_LANG_Ada95               : "DW_LANG_Ada95",
    DW_LANG_Fortran95           : "DW_LANG_Fortran95",
    DW_LANG_PLI                 : "DW_LANG_PLI",
    DW_LANG_ObjC                : "DW_LANG_ObjC",
    DW_LANG_ObjC_plus_plus      : "DW_LANG_ObjC_plus_plus",
    DW_LANG_UPC                 : "DW_LANG_UPC",
    DW_LANG_D                   : "DW_LANG_D",
    DW_LANG_Python              : "DW_LANG_Python",
    DW_LANG_lo_user             : "DW_LANG_lo_user",
    DW_LANG_hi_user             : "DW_LANG_hi_user",
}

class Language(Base):
    MAP = LANG_MAP

##
## Identifier case encodings.
##
DW_ID_case_sensitive            = 0x00
DW_ID_up_case                   = 0x01
DW_ID_down_case                 = 0x02
DW_ID_case_insensitive          = 0x03

ID_MAP = {
    DW_ID_case_sensitive        : "DW_ID_case_sensitive",
    DW_ID_up_case               : "DW_ID_up_case",
    DW_ID_down_case             : "DW_ID_down_case",
    DW_ID_case_insensitive      : "DW_ID_case_insensitive",
}

class IdentifierCase(Base):
    MAP = ID_MAP

##
## Calling convention encodings.
##
DW_CC_normal                    = 0x01
DW_CC_program                   = 0x02
DW_CC_nocall                    = 0x03
DW_CC_lo_user                   = 0x40
DW_CC_hi_user                   = 0xff

CC_MAP = {
    DW_CC_normal                : "DW_CC_normal",
    DW_CC_program               : "DW_CC_program",
    DW_CC_nocall                : "DW_CC_nocall",
    DW_CC_lo_user               : "DW_CC_lo_user",
    DW_CC_hi_user               : "DW_CC_hi_user",
}

class CallingConvention(Base):
    MAP = CC_MAP

##
## Inline encodings.
##
DW_INL_not_inlined              = 0x00
DW_INL_inlined                  = 0x01
DW_INL_declared_not_inlined     = 0x02
DW_INL_declared_inlined         = 0x03

INL_MAP = {
    DW_INL_not_inlined          : "DW_INL_not_inlined",
    DW_INL_inlined              : "DW_INL_inlined",
    DW_INL_declared_not_inlined : "DW_INL_declared_not_inlined",
    DW_INL_declared_inlined     : "DW_INL_declared_inlined",
}

class Inline(Base):
    MAP = INL_MAP


##
## Ordering encodings.
##
DW_ORD_row_major                = 0x00
DW_ORD_col_major                = 0x01

ORD_MAP = {
    DW_ORD_row_major            : "DW_ORD_row_major",
    DW_ORD_col_major            : "DW_ORD_col_major",
}

class Ordering(Base):
    MAP = ORD_MAP


##
##  Discriminant descriptor encodings.
##
DW_DSC_label                    = 0x00
DW_DSC_range                    = 0x01

DSC_MAP = {
    DW_DSC_label                : "DW_DSC_label",
    DW_DSC_range                : "DW_DSC_range",
}

class DiscriminantDescriptor(Base):
    MAP = DSC_MAP


##
##  Line Number Standard Opcode Encodings.
##
DW_LNS_copy                     = 0x01
DW_LNS_advance_pc               = 0x02
DW_LNS_advance_line             = 0x03
DW_LNS_set_file                 = 0x04
DW_LNS_set_column               = 0x05
DW_LNS_negate_stmt              = 0x06
DW_LNS_set_basic_block          = 0x07
DW_LNS_const_add_pc             = 0x08
DW_LNS_fixed_advance_pc         = 0x09
DW_LNS_set_prologue_end         = 0x0a
DW_LNS_set_epilogue_begin       = 0x0b
DW_LNS_set_isa                  = 0x0c

LNS_MAP = {
    DW_LNS_copy                 : "DW_LNS_copy",
    DW_LNS_advance_pc           : "DW_LNS_advance_pc",
    DW_LNS_advance_line         : "DW_LNS_advance_line",
    DW_LNS_set_file             : "DW_LNS_set_file",
    DW_LNS_set_column           : "DW_LNS_set_column",
    DW_LNS_negate_stmt          : "DW_LNS_negate_stmt",
    DW_LNS_set_basic_block      : "DW_LNS_set_basic_block",
    DW_LNS_const_add_pc         : "DW_LNS_const_add_pc",
    DW_LNS_fixed_advance_pc     : "DW_LNS_fixed_advance_pc",
    DW_LNS_set_prologue_end     : "DW_LNS_set_prologue_end",
    DW_LNS_set_epilogue_begin   : "DW_LNS_set_epilogue_begin",
    DW_LNS_set_isa              : "DW_LNS_set_isa",
}

class LineNumberStandard(Base):
    MAP = LNS_MAP


##
##  Line Number Extended Opcode Encodings.
##
DW_LNE_end_sequence             = 0x01
DW_LNE_set_address              = 0x02
DW_LNE_define_file              = 0x03
DW_LNE_set_discriminator        = 0x04
DW_LNE_lo_user                  = 0x80
DW_LNE_hi_user                  = 0xff

LNE_MAP = {
    DW_LNE_end_sequence         : "DW_LNE_end_sequence",
    DW_LNE_set_address          : "DW_LNE_set_address",
    DW_LNE_define_file          : "DW_LNE_define_file",
    DW_LNE_set_discriminator    : "DW_LNE_set_discriminator",
    DW_LNE_lo_user              : "DW_LNE_lo_user",
    DW_LNE_hi_user              : "DW_LNE_hi_user",
}


class LineNumberExtended(Base):
    MAP = LNE_MAP

##
## Macro Information.
##
DW_MACINFO_define               = 0x01
DW_MACINFO_undef                = 0x02
DW_MACINFO_start_file           = 0x03
DW_MACINFO_end_file             = 0x04
DW_MACINFO_vendor_ext           = 0xff

MACINFO_MAP = {
    DW_MACINFO_define           : "DW_MACINFO_define",
    DW_MACINFO_undef            : "DW_MACINFO_undef",
    DW_MACINFO_start_file       : "DW_MACINFO_start_file",
    DW_MACINFO_end_file         : "DW_MACINFO_end_file",
    DW_MACINFO_vendor_ext       : "DW_MACINFO_vendor_ext",
}

class MacroInformation(Base):
    MAP = MACINFO_MAP

##
## Segmented Addresses.
##

# For example, the Intel386 processor might use the following values:

DW_ADDR_none                    = 0x00
DW_ADDR_near16                  = 0x01
DW_ADDR_far16                   = 0x02
DW_ADDR_huge16                  = 0x03
DW_ADDR_near32                  = 0x04
DW_ADDR_far32                   = 0x05


class ExceptionHeaderEncoding(enum.IntEnum):
    """The DWARF Exception Header Encoding is used to describe the type of data
    used in the .eh_frame and .eh_frame_hdr section.

    Linux specific, s. Linux Base Standard.
    """
    DW_EH_PE_absptr     = 0x00
    DW_EH_PE_uleb128    = 0x01
    DW_EH_PE_udata2     = 0x02
    DW_EH_PE_udata4     = 0x03
    DW_EH_PE_udata8     = 0x04
    DW_EH_PE_sleb128    = 0x09
    DW_EH_PE_sdata2     = 0x0A
    DW_EH_PE_sdata4     = 0x0B
    DW_EH_PE_sdata8     = 0x0C
    DW_EH_PE_pcrel      = 0x10
    DW_EH_PE_textrel    = 0x20
    DW_EH_PE_datarel    = 0x30
    DW_EH_PE_funcrel    = 0x40
    DW_EH_PE_aligned    = 0x50


class CFIExtensions(enum.IntEnum):
    """
    """

    DW_CFA_GNU_args_size                = 0x2e
    DW_CFA_GNU_negative_offset_extended = 0x2f
