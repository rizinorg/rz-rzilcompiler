# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Effects.Empty import Empty
from Transformer.ILOpsHolder import OpCounter


class Sequence(Effect):

    def __init__(self, name, effects: list[Effect]):
        eff = list()
        for e in effects:
            if isinstance(e, Effect):
                eff.append(e)
        if len(eff) == 0:
            eff = [Empty(f'empty_seq_{OpCounter().get_op_count()}')]

        self.effects = eff
        self.effect_ops = self.effects
        Effect.__init__(self, name, EffectType.SEQUENCE)

    def il_write(self):
        return f'SEQN({len(self.effects)}, {", ".join([e.effect_var() for e in self.effects])})'
