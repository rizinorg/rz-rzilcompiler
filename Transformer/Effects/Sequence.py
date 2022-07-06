# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import Pure


class Sequence(Effect):

    def __init__(self, name, effects: list[Effect]):
        self.effects = effects
        Effect.__init__(self, name, EffectType.SEQUENCE)

    def il_write(self):
        return f'SEQN({", ".join([e.get_name() for e in self.effects])})'
