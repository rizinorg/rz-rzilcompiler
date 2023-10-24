# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Effects.Effect import Effect, EffectType
from rzil_compiler.Transformer.Effects.Empty import Empty


class Sequence(Effect):
    def __init__(self, name, effects: list[Effect]):
        eff = list()
        self.effect_ops = list()
        for e in effects:
            if isinstance(e, Effect):
                eff.append(e)
            else:
                self.effect_ops.append(e)
        if len(eff) == 0:
            eff = [Empty(f"empty_seq")]

        self.effects = eff
        self.effect_ops += self.effects
        Effect.__init__(self, name, EffectType.SEQUENCE)

    def il_write(self):
        if len(self.effects) == 1:
            return self.effects[0].effect_var()
        return f'SEQN({len(self.effects)}, {", ".join([e.effect_var() for e in self.effects])})'

    def __str__(self):
        seq = "; ".join([str(stmt) for stmt in self.effect_ops])
        if len(seq) > 60:
            return f"seq({seq[:60]} ..."
        return f"seq({seq})"
