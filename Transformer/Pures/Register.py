# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.PluginInfo import isa_to_reg_fnc, isa_to_reg_args, isa_alias_to_reg, isa_alias_to_reg_args
from Transformer.Pures.GlobalVar import GlobalVar
from enum import StrEnum

from Transformer.Pures.Pure import ValueType


class RegisterAccessType(StrEnum):
    R = 'SRC_REG'
    W = 'DEST_REG'
    RW = 'SRC_DEST_REG'
    PR = 'SRC_REG_PAIR'
    PW = 'DEST_REG_PAIR'
    PRW = 'SRC_DEST_REG_PAIR'


class Register(GlobalVar):

    def __init__(self, name: str, access: RegisterAccessType, v_type: ValueType, is_new: bool = False, is_explicit: bool = False, is_reg_alias: bool = False):
        self.access = access
        self.is_new = is_new
        self.is_explicit = is_explicit  # Register number is predefined by instruction.
        self.is_reg_alias = is_reg_alias

        if self.is_new:
            GlobalVar.__init__(self, name + '_tmp', v_type)
        else:
            GlobalVar.__init__(self, name, v_type)
        self.set_isa_name(name)

    def get_assoc_name(self, write_usage: bool):
        if write_usage:
            return self.name_assoc + '_tmp'
        return self.name_assoc

    def vm_id(self, write_usage: bool):
        # Global var names (registers mainly) are stored in "<reg>_assoc(_tmp)" variables.
        if self.is_explicit:
            if write_usage:
                return f'"{self.get_name()}_tmp"'
            return f'"{self.get_name()}"'

        if write_usage:
            return self.get_assoc_name(True)
        return self.get_assoc_name(False)

    def il_init_var(self):
        if self.is_explicit:
            return f'RzILOpPure *{self.pure_var()} = VARG({self.vm_id(False)});'

        # Registers which are only written do not need their own RzILOpPure.
        if self.access == RegisterAccessType.W or self.access == RegisterAccessType.PW:
            return self.il_isa_to_assoc_name(True)
        elif self.access == RegisterAccessType.RW or self.access == RegisterAccessType.PRW:
            init = self.il_isa_to_assoc_name(True) + '\n'
            init += self.il_isa_to_assoc_name(False) + '\n'
        elif self.is_reg_alias:
            init = self.il_reg_alias_to_hw_reg() + '\n'
        else:
            init = self.il_isa_to_assoc_name(False) + '\n'

        init += f'RzILOpPure *{self.pure_var()} = VARG({self.get_assoc_name(False)});'
        return init

    def il_isa_to_assoc_name(self, write_usage: bool) -> str:
        """ Returns code to: Translate a placeholder ISA name of an register (like Rs)
        to the real register name of the current instruction.
        E.g. Rs -> "R3"
        """
        return f'const char *{self.get_assoc_name(write_usage)} = {isa_to_reg_fnc}({", ".join(isa_to_reg_args)}, \'{self.get_isa_name()[1]}\', {str(self.is_new).lower()});'

    def il_reg_alias_to_hw_reg(self) -> str:
        """ Some registers are an alias for another register (PC = C9, GP = C11, SP = R29 etc.
            Unfortunately those alias can change from ISA version to ISA version.
            So the plugin needs to translate these. Here we return the code for this translation.
        """
        return f'const char *{self.name_assoc} = {isa_alias_to_reg}({", ".join(isa_alias_to_reg_args)}{", " if isa_alias_to_reg_args else ""}{self.get_alias_enum(self.name)});'

    def il_read(self) -> str:
        # There is a tricky case where write only register are read any ways in the semantic definitions.
        # We can detect those registers because Register.il_read() gets only called on readable registers.
        # So if this method is called on a write-only register we return the value of the .new register.
        # Examples: a2_svaddh, a4_vcmpbgt
        if self.access is RegisterAccessType.W or self.access is RegisterAccessType.PW:
            return f'VARG({self.vm_id(True)})'
        return GlobalVar.il_read(self)

    def get_pred_num(self) -> int:
        num = self.get_name()[-1]
        if self.get_name()[0].upper() != 'P' or num not in ['0', '1', '2', '3']:
            raise NotImplementedError(f'This function should only called for explicit predicate register. This is {self.get_name()}')
        return int(num)

    @staticmethod
    def get_alias_enum(alias: str) -> str:
        return f'HEX_REG_ALIAS_{alias.upper()}'
