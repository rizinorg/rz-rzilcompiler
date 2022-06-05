# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import Pure, PureType, ValueType


class GlobalVar(Pure):
    reads = None

    def __init__(self, name: str, v_type: ValueType):
        self.reads = 0
        super().__init__(name, PureType.GLOBAL, v_type)

    def il_init_var(self):
        init = self.il_isa_to_assoc_name()
        init += f'RzIlOpPure *{self.get_isa_name()} = VARG({self.get_isa_name()});'
        return init

    def il_read(self):
        if self.reads < 1:  # First use of this variable
            ret = self.get_isa_name()
        else:
            ret = f'DUP({self.get_isa_name()})'

        self.reads += 1
        return ret
