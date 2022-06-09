# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import Pure, ValueType
from Transformer.Pures.PureExec import PureExec
from Transformer.helper import exc_if_types_not_match


class Ternary(PureExec):

    def __init__(self, name: str, cond: Pure, then_p: Pure, else_p: Pure):
        exc_if_types_not_match(then_p.value_type, else_p.value_type)
        super().__init__(name, [cond, then_p, else_p], then_p.value_type)

    def il_exec(self):
        if self.value_type.signed:
            fill_bit = f'MSB({self.ops[0].il_read()})'
        else:
            fill_bit = 'IL_FALSE'
        return f'CAST({self.value_type.bit_width}, {fill_bit}, {self.ops[0].il_read()})'
