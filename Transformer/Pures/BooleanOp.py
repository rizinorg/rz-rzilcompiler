# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pures.Pure import Pure
from Transformer.Pures.PureExec import PureExec


class BooleanType(StrEnum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'


class ArithmeticOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, a_type: ArithmeticType):
        self.a = a
        self.b = b
        self.a_type = a_type

        super().__init__(name, max(self.avalue_type.bit_width, self.bvalue_type.bit_width))

    def il_exec(self):
        if self.a_type == ArithmeticType.ADD:
            return f'ADD({self.a.il_read()}, {self.b.il_read()}'
        elif self.a_type == ArithmeticType.SUB:
            return f'SUB({self.a.il_read()}, {self.b.il_read()}'
        elif self.a_type == ArithmeticType.MUL:
            return f'MUL({self.a.il_read()}, {self.b.il_read()}'
        elif self.a_type == ArithmeticType.DIV:
            return f'DIV({self.a.il_read()}, {self.b.il_read()}'
        elif self.a_type == ArithmeticType.MOD:
            return f'MOD({self.a.il_read()}, {self.b.il_read()}'
        else:
            raise NotImplementedError('')
