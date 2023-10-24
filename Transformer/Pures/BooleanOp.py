# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from rzil_compiler.Transformer.Pures.CompareOp import CompareOp
from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.Pures.PureExec import PureExec


class BooleanOpType(StrEnum):
    AND = "&&"
    OR = "||"
    INV = "!"


class BooleanOp(PureExec):
    def __init__(self, name: str, a: Pure, b: Pure, op_type: BooleanOpType):
        self.op_type = op_type

        if b:
            PureExec.__init__(self, name, [a, b], a.value_type)
        else:
            PureExec.__init__(self, name, [a], a.value_type)

    def il_exec(self):
        a = (
            self.ops[0].il_read()
            if (
                isinstance(self.ops[0], BooleanOp) or isinstance(self.ops[0], CompareOp)
            )
            else f"NON_ZERO({self.ops[0].il_read()})"
        )
        if self.op_type == BooleanOpType.INV:
            return f"INV({a})"

        b = (
            self.ops[1].il_read()
            if (
                isinstance(self.ops[1], BooleanOp) or isinstance(self.ops[1], CompareOp)
            )
            else f"NON_ZERO({self.ops[1].il_read()})"
        )
        if self.op_type == BooleanOpType.AND:
            return f"AND({a}, {b})"
        elif self.op_type == BooleanOpType.OR:
            return f"OR({a}, {b})"
        else:
            raise NotImplementedError(
                f"Boolean operation {self.op_type} not implemented."
            )

    def __str__(self):
        if self.op_type == BooleanOpType.INV:
            return f"{self.op_type} {self.ops[0]}"
        return f"{self.ops[0]} {self.op_type} {self.ops[1]}"
