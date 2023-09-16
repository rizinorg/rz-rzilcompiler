# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.Pures.PureExec import PureExec
from rzil_compiler.Transformer.Pures.BooleanOp import BooleanOp
from rzil_compiler.Transformer.Pures.CompareOp import CompareOp


class Ternary(PureExec):
    def __init__(self, name: str, cond: Pure, then_p: Pure, else_p: Pure):
        PureExec.__init__(self, name, [cond, then_p, else_p], then_p.value_type)

    def il_exec(self):
        if isinstance(self.ops[0], BooleanOp) or isinstance(self.ops[0], CompareOp):
            cond = self.ops[0].il_read()
        else:
            cond = f"NON_ZERO({self.ops[0].il_read()})"
        return f"ITE({cond}, {self.ops[1].il_read()}, {self.ops[2].il_read()})"
