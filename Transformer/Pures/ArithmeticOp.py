# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.Pures.PureExec import PureExec
from rzil_compiler.Transformer.helper import cast_operands


class ArithmeticType(StrEnum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"


class ArithmeticOp(PureExec):
    def __init__(self, name: str, a: Pure, b: Pure, arith_type: ArithmeticType):
        self.arith_type = arith_type
        if arith_type != ArithmeticType.MOD:
            # Modular operations don't need matching types.
            a, b = cast_operands(a=a, b=b, immutable_a=False)

        PureExec.__init__(self, name, [a, b], a.value_type)

    def il_exec(self):
        if self.arith_type == ArithmeticType.ADD:
            return f"ADD({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.arith_type == ArithmeticType.SUB:
            return f"SUB({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.arith_type == ArithmeticType.MUL:
            return f"MUL({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.arith_type == ArithmeticType.DIV:
            return f"DIV({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.arith_type == ArithmeticType.MOD:
            return f"MOD({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        else:
            raise NotImplementedError(f"Arithmetic type {self.arith_type} not handled.")
