# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pures.Pure import Pure
from Transformer.Pures.PureExec import PureExec


class ShiftOpType(StrEnum):
    RSHIFT = '>>'
    LSHIFT = '<<'


class ShiftOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, shift_type: ShiftOpType):
        self.a = a
        self.b = b
        self.shift_type = shift_type

        super().__init__(name, [a, b], self.a.value_type)

    def il_exec(self):
        if self.shift_type == ShiftOpType.RSHIFT:
            return f'SHIFTR0({self.a.il_read()}, {self.b.il_read()}'
        elif self.shift_type == ShiftOpType.LSHIFT:
            return f'SHIFTL0({self.a.il_read()}, {self.b.il_read()}'
        else:
            raise NotImplementedError(f'Shift op {self.shift_type} not implemented.')
