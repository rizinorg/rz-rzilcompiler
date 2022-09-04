# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.ILOpsHolder import OpCounter
from Transformer.Pures.Cast import Cast
from Transformer.Pures.Pure import Pure
from Transformer.Pures.PureExec import PureExec
from Transformer.helper import check_and_convert_types


class BitOperationType(StrEnum):
    OR = "|"
    AND = "&"
    XOR = "^"
    NOT = "~"
    NEG = "-"
    RSHIFT = '>>'
    LSHIFT = '<<'


class BitOp(PureExec):
    def __init__(self, name: str, a: Pure, b: Pure, op_type: BitOperationType):
        a_casted = None
        b_casted = None
        if (a and b) and not (op_type == BitOperationType.RSHIFT or op_type == BitOperationType.LSHIFT):
            # No need to check for single operand operations.
            a_casted, b_casted = check_and_convert_types(a.value_type, b.value_type)
        self.op_type = op_type

        if a_casted and b_casted:
            cname = f'cast_{OpCounter().get_op_count()}'
            if a_casted.bit_width != a.value_type.bit_width or a_casted.signed != a.value_type.signed:
                a = Cast(cname, a_casted, a)
            if b_casted.bit_width != b.value_type.bit_width or b_casted.signed != b.value_type.signed:
                b = Cast(cname, b_casted, b)

        if a_casted:
            PureExec.__init__(self, name, [a, b], a_casted)
        elif b:
            PureExec.__init__(self, name, [a, b], a.value_type)
        else:
            PureExec.__init__(self, name, [a], a.value_type)

    def il_exec(self):
        if self.op_type == BitOperationType.AND:
            return f"LOGAND({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == BitOperationType.OR:
            return f"LOGOR({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == BitOperationType.XOR:
            return f"LOGXOR({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == BitOperationType.NOT:
            return f"LOGNOT({self.ops[0].il_read()})"
        elif self.op_type == BitOperationType.NEG:
            return f"NEG({self.ops[0].il_read()})"
        elif self.op_type == BitOperationType.RSHIFT:
            return f'SHIFTR0({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        elif self.op_type == BitOperationType.LSHIFT:
            return f'SHIFTL0({self.ops[0].il_read()}, {self.ops[1].il_read()})'
        else:
            raise NotImplementedError("")
