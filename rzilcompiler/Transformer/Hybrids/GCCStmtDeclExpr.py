# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzilcompiler.Transformer.Effects.Effect import Effect
from rzilcompiler.Transformer.Hybrids.Hybrid import HybridType, Hybrid, HybridSeqOrder
from rzilcompiler.Transformer.Pures.Pure import Pure
from rzilcompiler.Transformer.ValueType import ValueType


class GCCStmtDeclExpr(Hybrid):
    """
    This implements the GCC extension of statements and declare expressions"
    https://gcc.gnu.org/onlinedocs/gcc-2.95.3/gcc_4.html#SEC62
    """

    def __init__(self, name: str, stmt: Effect, expr: Pure, value_type: ValueType):
        self.op_type = HybridType.GCC_EXPR
        self.stmt: Effect = stmt
        self.expr: Pure = expr
        self.seq_order = HybridSeqOrder.EXEC_THEN_SET_VAL

        Hybrid.__init__(self, name, [stmt, expr], value_type)

    def update_stmt(self, stmt: Effect):
        self.stmt = stmt
        self.effect_ops[0] = stmt

    def il_write(self):
        return self.stmt.il_write()

    def il_exec(self):
        return self.stmt.il_exec()

    def il_read(self):
        return self.expr.il_read()
