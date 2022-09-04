# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pures.Pure import Pure
from Transformer.Pures.PureExec import PureExec
from Transformer.helper import cast_operands


class BooleanOpType(StrEnum):
    AND = '&&'
    OR = '||'
    INV = '~'


class BooleanOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, op_type: BooleanOpType):
        self.op_type = op_type
        if a and b:
            # No need to check for single operand operations.
            a, b = cast_operands(a=a, b=b, immutable_a=False)

        if b:
            PureExec.__init__(self, name, [a, b], a.value_type)
        else:
            PureExec.__init__(self, name, [a], a.value_type)

    def il_exec(self):
        if self.op_type == BooleanOpType.AND:
            return f'ADD({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.op_type == BooleanOpType.OR:
            return f'OR({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.op_type == BooleanOpType.INV:
            return f'INV({self.ops[0].il_read()})'
        else:
            raise NotImplementedError(f'Boolean operation {self.op_type} not implemented.')
