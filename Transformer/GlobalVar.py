# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pure import Pure, PureType
from Transformer.PluginInfo import isa_to_reg_fnc, isa_to_reg_args


class GlobalVar(Pure):
    reads = None

    def __init__(self, name: str):
        self.reads = 0
        super().__init__(name, PureType.GLOBAL)

    def code_init_var(self):
        init = self.code_isa_to_assoc_name()
        init += f'RzIlOpPure *{self.get_isa_name()} = VARG({self.get_isa_name()});'
        return init

    def code_read(self):
        if self.reads < 1: # First use of this variable
            ret = self.get_isa_name()
        else:
            ret = f'DUP({self.get_isa_name()})'

        self.reads += 1
        return ret