# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pure import Pure
from Transformer.Pures.PureExec import PureExec


class ArithmeticType(StrEnum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'


class ArithmeticOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, atype: ArithmeticType):
        self.a = a
        self.b = b
        self.a_type = atype

        super().__init__(name, max(self.a.size, self.b.size))

    def il_exec(self):
        if self.a_type == ArithmeticType.ADD:
            return f'ADD({self.a.il_read()}, {self.b.il_read()}'
        elif self.a_type == ArithmeticType.SUB:
            return f'SUB({self.a.il_read()}, {self.b.il_read()}'
        else:
            NotImplementedError('')
