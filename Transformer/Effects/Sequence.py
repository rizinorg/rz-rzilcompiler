# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import Pure


class Sequence(Effect):

    def __init__(self, name, effects: list[Effect]):
        for e in effects:
            if not isinstance(e, Effect):
                raise NotImplementedError(f'{e.get_name()} is not an effect but was given to a sequence.')
        self.effects = effects
        Effect.__init__(self, name, EffectType.SEQUENCE)

    def il_write(self):
        return f'SEQN({len(self.effects)}, {", ".join([e.effect_var() for e in self.effects])})'
