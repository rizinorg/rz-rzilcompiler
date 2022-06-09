# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.Pures.Immediate import Immediate
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.Pure import ValueType
from Transformer.Pures.Register import RegisterAccessType, Register
from Transformer.TransformerExtension import TransformerExtension
from Transformer.helper_hexagon import get_value_type_from_reg_type, get_value_type_by_isa_imm, get_value_type_by_c_type
from lark import Token


class HexagonExtension(TransformerExtension):

    uses_new = False
    writes_mem = False
    reads_mem = False
    is_conditional = False
    branches = False

    def __init__(self):
        self.special_identifiers = ['EA']

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
        if alias == 'UPCYCLE' or alias == 'PKTCOUNT' or alias == 'UTIMER':
            size = 64
        else:
            size = 32
        v_type = ValueType(False, size)
        return Register(alias.lower(), RegisterAccessType.RW, v_type, is_reg_alias=True)

    def reg(self, items):
        return self.hex_reg(items, False)

    def hex_reg(self, items, is_new: bool):
        holder = ILOpsHolder()
        items: [Token]
        name = ''.join(items)
        reg_type = items[1].type  # src, dest, both
        v_type = get_value_type_from_reg_type(items)

        if reg_type == RegisterAccessType.R or reg_type == RegisterAccessType.PR:
            # Should be read before use. Add to read list.
            if name in holder.read_ops:
                return holder.read_ops[name]
            v = Register(name, RegisterAccessType.R, v_type, is_new)
        elif reg_type == RegisterAccessType.W or reg_type == RegisterAccessType.PW:
            # Dest regs are passed as string to SETG(). Need no Pure variable.
            if name in holder.read_ops:
                return holder.read_ops[name]
            v = Register(name, RegisterAccessType.W, v_type, is_new)
        elif reg_type == RegisterAccessType.RW or reg_type == RegisterAccessType.PRW:
            if name in holder.read_ops:
                return holder.read_ops[name]
            v = Register(name, RegisterAccessType.RW, v_type, is_new)
        else:
            raise NotImplementedError(f'Reg type "{reg_type.name}" not implemented.')
        v.set_isa_name(name)
        return v

    def imm(self, items):
        v_type = get_value_type_by_isa_imm(items)
        name = f'{items[0]}'
        imm = Immediate(name, v_type)
        imm.set_isa_name(name)
        return imm

    def get_value_type_by_resource_type(self, t):
        return get_value_type_by_c_type(t)

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
        if fcn_name == 'hex_next_pc':
            return ValueType(False, 32)
        else:
            raise NotImplementedError(f'No value type for function {fcn_name} defined.')

    def special_identifier_to_local_var(self, identifier):
        if identifier == 'EA':
            return LocalVar('EA', ValueType(False, 32))
