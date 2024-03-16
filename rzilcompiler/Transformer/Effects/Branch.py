# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzilcompiler.Transformer.Effects.Effect import Effect, EffectType
from rzilcompiler.Transformer.Pures.Pure import Pure
from rzilcompiler.Transformer.Pures.BooleanOp import BooleanOp
from rzilcompiler.Transformer.Pures.CompareOp import CompareOp


class Branch(Effect):
    def __init__(self, name: str, cond: Pure, then: Effect, otherwise: Effect):
        self.cond = cond
        self.then = then
        self.otherwise = otherwise
        self.effect_ops = [self.cond, self.then, self.otherwise]
        Effect.__init__(self, name, EffectType.BRANCH)

    def il_write(self):
        """Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        if isinstance(self.cond, BooleanOp) or isinstance(self.cond, CompareOp):
            cond = self.cond.il_read()
        else:
            cond = f"NON_ZERO({self.cond.il_read()})"
        return (
            f"BRANCH({cond}, {self.then.effect_var()}, {self.otherwise.effect_var()})"
        )

    def __str__(self):
        return f"if ({self.cond}) {{{self.then}}}{f' else {{{self.otherwise}}}' if self.otherwise else ''}"
