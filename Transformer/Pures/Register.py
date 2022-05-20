# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.PluginInfo import isa_to_reg_fnc, isa_to_reg_args
from Transformer.Pures.GlobalVar import GlobalVar
from enum import StrEnum


class RegisterAccessType(StrEnum):
    R = 'SRC_REG'
    W = 'DEST_REG'
    RW = 'SRC_DEST_REG'
    PR = 'SRC_REG_PAIR'
    PW = 'DEST_REG_PAIR'
    PRW = 'SRC_DEST_REG_PAIR'


class Register(GlobalVar):

    def __init__(self, name: str, access: RegisterAccessType, size: int):
        self.access = access
        super().__init__(name, size)

    def il_init_var(self):
        if self.access == RegisterAccessType.W:  # Registers which are only written do not need an own RzILOpPure.
            return self.il_isa_to_assoc_name()
        init = self.il_isa_to_assoc_name() + '\n'
        init += f'RzIlOpPure *{self.get_isa_name()} = VARG({self.get_assoc_name()});'
        return init

    def il_isa_to_assoc_name(self):
        return f'const char *{self.name_assoc} = {isa_to_reg_fnc}({", ".join(isa_to_reg_args)}, "{self.name}");'
