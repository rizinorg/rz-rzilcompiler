# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pures.Pure import Pure
from Transformer.Pures.PureExec import PureExec
from Transformer.helper import exc_if_types_not_match


class BooleanType(StrEnum):
    AND = '&&'
    OR = '||'
    INV = '~'


class ArithmeticOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, op_type: BooleanType):
        if a and b:
            # No need to check for single operand operations.
            exc_if_types_not_match(a.value_type, b.value_type)
        self.op_type = op_type

        if b:
            super().__init__(name, [a, b], a.value_type)
        else:
            super().__init__(name, [a], a.value_type)

    def il_exec(self):
        if self.op_type == BooleanType.AND:
            return f'ADD({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.op_type == BooleanType.OR:
            return f'OR({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.op_type == BooleanType.INV:
            return f'INV({self.ops[0].il_read()})'
        else:
            raise NotImplementedError(f'Boolean operation {self.op_type} not implemented.')
