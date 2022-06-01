# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pures.Pure import Pure
from Transformer.Pures.PureExec import PureExec


class ArithmeticType(StrEnum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'


class ArithmeticOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, a_type: ArithmeticType):
        self.a_type = a_type

        super().__init__(name, [a, b])

    def il_exec(self):
        if self.a_type == ArithmeticType.ADD:
            return f'ADD({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        elif self.a_type == ArithmeticType.SUB:
            return f'SUB({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        elif self.a_type == ArithmeticType.MUL:
            return f'MUL({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        elif self.a_type == ArithmeticType.DIV:
            return f'DIV({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        elif self.a_type == ArithmeticType.MOD:
            return f'MOD({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        else:
            raise NotImplementedError('')
