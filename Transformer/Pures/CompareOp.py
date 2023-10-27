# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from rzil_compiler.Transformer.ValueType import ValueType, VTGroup
from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.Pures.PureExec import PureExec


class CompareOpType(StrEnum):
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    EQ = "=="
    NE = "!="


class CompareOp(PureExec):
    def __init__(self, name: str, a: Pure, b: Pure, op_type: CompareOpType):
        self.op_type = op_type

        PureExec.__init__(
            self, name, [a, b], ValueType(False, 1, VTGroup.PURE | VTGroup.BOOL)
        )

    def il_exec(self):
        sl = (
            "S"
            if (self.ops[0].value_type.signed or self.ops[1].value_type.signed)
            else "U"
        )
        if self.op_type == CompareOpType.LT:
            return f"{sl}LT({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.GT:
            return f"{sl}GT({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.LE:
            return f"{sl}LE({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        if self.op_type == CompareOpType.GE:
            return f"{sl}GE({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.EQ:
            return f"EQ({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.NE:
            return f"INV(EQ({self.ops[0].il_read()}, {self.ops[1].il_read()}))"
        else:
            raise NotImplementedError(
                f"Compare operation {self.op_type} not implemented."
            )

    def __str__(self):
        return f"({self.ops[0]} {self.op_type} {self.ops[1]})"
