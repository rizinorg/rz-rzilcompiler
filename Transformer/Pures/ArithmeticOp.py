# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.ILOpsHolder import OpCounter
from Transformer.Pures.Pure import Pure
from Transformer.Pures.Cast import Cast
from Transformer.Pures.PureExec import PureExec
from Transformer.helper import check_and_convert_types


class ArithmeticType(StrEnum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'


class ArithmeticOp(PureExec):

    def __init__(self, name: str, a: Pure, b: Pure, arith_type: ArithmeticType):
        a_casted = None
        b_casted = None
        if arith_type != ArithmeticType.MOD:
            # Modular operations don't need matching types.
            a_casted, b_casted = check_and_convert_types(a.value_type, b.value_type)
        self.arith_type = arith_type

        if a_casted and b_casted:
            cname = f'cast_{OpCounter().get_op_count()}'
            if a_casted.bit_width != a.value_type.bit_width or a_casted.signed != a.value_type.signed:
                a = Cast(cname, a_casted, a)
            if b_casted.bit_width != b.value_type.bit_width or b_casted.signed != b.value_type.signed:
                b = Cast(cname, b_casted, b)

        if a_casted:
            PureExec.__init__(self, name, [a, b], a_casted)
        else:
            PureExec.__init__(self, name, [a, b], a.value_type)

    def il_exec(self):
        if self.arith_type == ArithmeticType.ADD:
            return f'ADD({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.arith_type == ArithmeticType.SUB:
            return f'SUB({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.arith_type == ArithmeticType.MUL:
            return f'MUL({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.arith_type == ArithmeticType.DIV:
            return f'DIV({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.arith_type == ArithmeticType.MOD:
            return f'MOD({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        else:
            raise NotImplementedError(f'Arithmetic type {self.arith_type} not handled.')
