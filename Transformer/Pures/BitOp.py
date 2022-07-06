# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from Transformer.Pures.Number import Number
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
        if (a and b) and not (op_type == BitOperationType.RSHIFT or op_type == BitOperationType.LSHIFT):
            # No need to check for single operand operations.
            a.value_type, b.value_type = check_and_convert_types(a.value_type, b.value_type)
        self.op_type = op_type

        if b:
            if a.value_type.bit_width >= b.value_type.bit_width:
                if isinstance(b, Number):
                    b.value_type.bit_width = a.value_type.bit_width
                val_type = a.value_type
            else:
                if isinstance(a, Number):
                    a.value_type.bit_width = b.value_type.bit_width
                val_type = b.value_type
            PureExec.__init__(self, name, [a, b], val_type)
        else:
            PureExec.__init__(self, name, [a], a.value_type)

    def il_exec(self):
        if self.op_type == BitOperationType.AND:
            return f"LOGAND({self.ops[0].il_read()}, {self.ops[1].il_read()}"
        elif self.op_type == BitOperationType.OR:
            return f"LOGOR({self.ops[0].il_read()}, {self.ops[1].il_read()}"
        elif self.op_type == BitOperationType.XOR:
            return f"LOGXOR({self.ops[0].il_read()}, {self.ops[1].il_read()}"
        elif self.op_type == BitOperationType.NOT:
            return f"LOGNOT({self.ops[0].il_read()}"
        elif self.op_type == BitOperationType.NEG:
            return f"NEG({self.ops[0].il_read()}"
        elif self.op_type == BitOperationType.RSHIFT:
            return f'SHIFTR0({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        elif self.op_type == BitOperationType.LSHIFT:
            return f'SHIFTL0({self.ops[0].il_read()}, {self.ops[1].il_read()}'
        else:
            raise NotImplementedError("")
