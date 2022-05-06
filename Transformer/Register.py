# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pure import Pure, PureType
from Transformer.PluginInfo import isa_to_reg_fnc, isa_to_reg_args
from Transformer.GlobalVar import GlobalVar
from enum import Enum

class RegisterAccessType(Enum):
    R = 1
    W = 2
    RW = 3

class Register(GlobalVar):

    access = None

    def __init__(self, name: str, access: RegisterAccessType):
        self.access = access
        super().__init__(name)

    def code_init_var(self):
        if self.access == RegisterAccessType.W: # Registers which are are only written do not need an own RzILOpPure.
            return self.code_isa_to_assoc_name()
        init = self.code_isa_to_assoc_name() + '\n'
        init += f'RzIlOpPure *{self.get_isa_name()} = VARG({self.get_isa_name()});'
        return init

    def code_isa_to_assoc_name(self):
        return f'const char *{self.name_assoc} = {isa_to_reg_fnc}({", ".join(isa_to_reg_args)}, "{self.name}");'
