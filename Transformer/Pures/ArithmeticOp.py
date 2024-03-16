# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from rzil_compiler.Transformer.ValueType import VTGroup, FloatFormat
from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.Pures.PureExec import PureExec


class ArithmeticType(StrEnum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"


class ArithmeticOp(PureExec):
    def __init__(self, name: str, a: Pure, b: Pure, arith_type: ArithmeticType):
        self.arith_type = arith_type
        PureExec.__init__(self, name, [a, b], a.value_type)

    def il_exec(self):
        if self.arith_type == ArithmeticType.ADD:
            code = f"ADD("
        elif self.arith_type == ArithmeticType.SUB:
            code = f"SUB("
        elif self.arith_type == ArithmeticType.MUL:
            code = f"MUL("
        elif self.arith_type == ArithmeticType.DIV:
            code = f"DIV("
        elif self.arith_type == ArithmeticType.MOD:
            code = f"MOD("
        else:
            raise NotImplementedError(f"Arithmetic type {self.arith_type} not handled.")
        if (
            self.ops[0].value_type.group & VTGroup.FLOAT
            and self.ops[1].value_type.group & VTGroup.FLOAT
        ):
            return f"F{code}HEX_GET_INSN_RMODE(hi), {self.ops[0].il_read()}, {self.ops[1].il_read()})"
        return f"{code}{self.ops[0].il_read()}, {self.ops[1].il_read()})"

    def __str__(self):
        return f"{self.ops[0]} {self.arith_type} {self.ops[1]}"
