# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pures.Pure import Pure
from Transformer.Pures.PureExec import PureExec


class BitOperationType(StrEnum):
    BIT_OR_OP = '|'
    BIT_AND_OP = '&'
    BIT_XOR_OP = '^'
    BIT_NOT_OP = '~'


class BitOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, op_type: BitOperationType):
        self.a = a
        self.b = b
        self.op_type = op_type

        super().__init__(name, max(self.a.size, self.b.size) if self.b is not None else self.a.size)

    def il_exec(self):
        if self.op_type == BitOperationType.BIT_AND_OP:
            return f'LOGAND({self.a.il_read()}, {self.b.il_read()}'
        elif self.op_type == BitOperationType.BIT_OR_OP:
            return f'LOGOR({self.a.il_read()}, {self.b.il_read()}'
        elif self.op_type == BitOperationType.BIT_XOR_OP:
            return f'LOGXOR({self.a.il_read()}, {self.b.il_read()}'
        elif self.op_type == BitOperationType.BIT_NOT_OP:
            return f'LOGNOT({self.a.il_read()}'
        else:
            NotImplementedError('')
