# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pures.Pure import Pure
from Transformer.Pures.PureExec import PureExec


class ShiftOpType(StrEnum):
    RSHIFT = '>>'
    LSHIFT = '<<'


class ShiftOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, op_type: ShiftOpType):
        self.op_type = op_type

        super().__init__(name, [a, b], a.value_type)

    def il_exec(self):
        if self.op_type == ShiftOpType.RSHIFT:
            return f'SHIFTR0({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        elif self.op_type == ShiftOpType.LSHIFT:
            return f'SHIFTL0({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        else:
            raise NotImplementedError(f'Shift op {self.op_type} not implemented.')
