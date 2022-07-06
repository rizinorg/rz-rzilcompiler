# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.Pures.Immediate import Immediate
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.Pure import ValueType
from Transformer.Pures.Register import RegisterAccessType, Register
from Transformer.TransformerExtension import TransformerExtension
from Transformer.helper_hexagon import get_value_type_from_reg_type, get_value_type_by_isa_imm
from lark import Token, Tree


class HexagonExtension(TransformerExtension):

    uses_new = False
    writes_mem = False
    reads_mem = False
    is_conditional = False
    branches = False

    def __init__(self):
        # Variables names used in the shortcode with special meaning.
        self.special_identifiers = {'EffectiveAddress': 'EA', 'iterator_i': 'i'}

    def set_uses_new(self):
        if not self.uses_new:
            self.uses_new = True

    def set_writes_mem(self):
        if not self.writes_mem:
            self.writes_mem = True

    def set_reads_mem(self):
        if not self.reads_mem:
            self.reads_mem = True

    def set_is_conditional(self):
        if not self.is_conditional:
            self.is_conditional = True

    def set_branches(self):
        if not self.branches:
            self.branches = True

    def set_token_meta_data(self, token: str):
        if token == 'mem_store':
            self.set_writes_mem()
        elif token == 'mem_load':
            self.set_reads_mem()
        elif token == 'new_reg':
            self.set_uses_new()
        elif token == 'jump':
            self.set_branches()

    def reg_alias(self, items):
        alias = items[0]
        is_new = False
        if len(items) == 2:
            is_new = True
        if alias == 'UPCYCLE' or alias == 'PKTCOUNT' or alias == 'UTIMER':
            size = 64
        else:
            size = 32
        v_type = ValueType(False, size)
        return Register(alias.lower(), RegisterAccessType.RW, v_type, is_new=is_new, is_reg_alias=True)

    def reg(self, items):
        return self.hex_reg(items, False)

    def hex_reg(self, items, is_new: bool, is_explicit: bool = False):
        holder = ILOpsHolder()
        items: [Token]
        if is_explicit:
            # If the register is explicitly given (R31, P1, P2 etc.)
            # The name is always the last in the list.
            name = items[-1]
        else:
            name = ''.join(items)
        reg_type = RegisterAccessType(items[1].type)  # src, dest, both
        v_type = get_value_type_from_reg_type(items)

        if reg_type in [RegisterAccessType.R, RegisterAccessType.PR]:
            if name in holder.read_ops:
                return holder.read_ops[name]
        elif reg_type in [RegisterAccessType.W, RegisterAccessType.PW]:
            if name in holder.read_ops:
                return holder.read_ops[name]
        elif reg_type in [RegisterAccessType.RW, RegisterAccessType.PRW]:
            if name in holder.read_ops:
                return holder.read_ops[name]
        else:
            raise NotImplementedError(f'Reg type "{reg_type.name}" not implemented.')

        v = Register(name, reg_type, v_type, is_new)
        v.set_isa_name(name)
        return v

    def imm(self, items):
        v_type = get_value_type_by_isa_imm(items)
        name = f'{items[0]}'
        imm = Immediate(name, v_type)
        imm.set_isa_name(name)
        return imm

    def get_value_type_by_resource_type(self, items):
        items: Tree = items[0]
        rule = items.data
        tokens = items.children
        if rule == 'c_size_type':
            return ValueType(tokens[1] == 's', int(tokens[0]))
        elif rule == 'c_int_type':
            return ValueType(tokens[0] == 'int', int(tokens[1]))
        else:
            raise NotImplementedError(f'Data type {rule} is not handled.')

    def get_meta(self):
        flags = []
        if self.is_conditional:
            flags.append('HEX_IL_INSN_ATTR_COND')
        if self.uses_new:
            flags.append('HEX_IL_INSN_ATTR_NEW')
        if self.writes_mem:
            flags.append('HEX_IL_INSN_ATTR_MEM_WRITE')
        if self.reads_mem:
            flags.append('HEX_IL_INSN_ATTR_MEM_READ')
        if self.branches:
            flags.append('HEX_IL_INSN_ATTR_BRANCH')
        if len(flags) == 0:
            flags.append('HEX_IL_INSN_ATTR_NONE')

        return flags

    def get_val_type_by_fcn(self, fcn_name: str):
        if fcn_name == 'hex_get_npc':
            return ValueType(False, 32)
        elif fcn_name == 'REGFIELD':
            # Register field macros. Calls a function which returns the width or
            # offset into the register of the field.
            return ValueType(False, 32)
        elif fcn_name == 'clo32':
            # QEMU function -- uint32_t clo32(uint32_t val)
            # Count leading ones in 32 bit value.
            return ValueType(False, 32)
        elif fcn_name == 'deposit64':
            # QEMU function
            # uint64_t deposit64(uint64_t value, int start, int length, uint64_t fieldval)
            # Sets the bits from 'start' to 'start+length' in 'value' with 'fieldvar'
            return ValueType(False, 64)
        elif fcn_name == 'sextract64':
            # QEMU function
            # "Extract from the 64 bit input @value the bit field specified by the
            # @start and @length parameters, and return it, sign extended to
            # an int64_t".
            return ValueType(True, 64)
        else:
            raise NotImplementedError(f'No value type for function {fcn_name} defined.')

    def special_identifier_to_local_var(self, identifier):
        if identifier == self.special_identifiers['EffectiveAddress']:
            return LocalVar('EA', ValueType(False, 32))
        elif identifier == self.special_identifiers['iterator_i']:
            return LocalVar('i', ValueType(False, 32))
