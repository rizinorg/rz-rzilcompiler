# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import StrEnum

from rzilcompiler.Transformer.Pures.Pure import Pure
from rzilcompiler.Transformer.Pures.PureExec import PureExec


class BitOperationType(StrEnum):
    OR = "|"
    AND = "&"
    XOR = "^"
    NOT = "~"
    NEG = "-"
    RSHIFT = ">>"
    LSHIFT = "<<"


class BitOp(PureExec):
    def __init__(self, name: str, a: Pure, b: Pure, op_type: BitOperationType):
        self.op_type = op_type

        if b:
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
            if self.ops[0].value_type.signed:
                # QEMU relies on right shift of signed integers to be arithmetic.
                return f"SHIFTRA({self.ops[0].il_read()}, {self.ops[1].il_read()})"
            else:
                return f"SHIFTR0({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        elif self.op_type == BitOperationType.LSHIFT:
            return f"SHIFTL0({self.ops[0].il_read()}, {self.ops[1].il_read()})"
        else:
            raise NotImplementedError("")

    def __str__(self):
        if self.op_type in [BitOperationType.NOT, BitOperationType.NEG]:
            return f"({self.op_type}{self.ops[0]})"
        return f"({self.ops[0]} {self.op_type} {self.ops[1]})"
