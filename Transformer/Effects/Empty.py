# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import Pure


class Empty(Effect):

    def __init__(self, name):
        Effect.__init__(self, name, EffectType.EMPTY)

    def il_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """

        return 'EMPTY()'
