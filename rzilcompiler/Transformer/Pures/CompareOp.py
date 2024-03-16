# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from rzilcompiler.Transformer.ValueType import ValueType, VTGroup
from rzilcompiler.Transformer.Pures.Pure import Pure
from rzilcompiler.Transformer.Pures.PureExec import PureExec


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
        is_float = False
        sl = (
            "S"
            if (self.ops[0].value_type.signed or self.ops[1].value_type.signed)
            else "U"
        )

        if (
            self.ops[0].value_type.group & VTGroup.FLOAT
            and self.ops[1].value_type.group & VTGroup.FLOAT
        ):
            is_float = True
            sl = ""

        if self.op_type == CompareOpType.LT:
            code = f"{sl}LT({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.GT:
            code = f"{sl}GT({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.LE:
            code = f"{sl}LE({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.GE:
            code = f"{sl}GE({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.EQ:
            code = f"EQ({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == CompareOpType.NE:
            code = f"INV(EQ({self.ops[0].il_read()}, {self.ops[1].il_read()}))"
        else:
            raise NotImplementedError(
                f"Compare operation {self.op_type} not implemented."
            )
        if is_float:
            return f"F{code}"
        return code

    def __str__(self):
        return f"({self.ops[0]} {self.op_type} {self.ops[1]})"
