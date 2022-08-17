# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import Pure


class Branch(Effect):

    def __init__(self, name: str, cond: Pure, then: Effect, otherwise: Effect):
        self.cond = cond
        self.then = then
        self.otherwise = otherwise
        Effect.__init__(self, name, EffectType.BRANCH)

    def il_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """

        return f'BRANCH({self.cond.get_name()}, {self.then.effect_var()}, {self.otherwise.effect_var()})'
