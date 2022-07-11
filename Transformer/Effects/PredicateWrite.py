# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import Pure
from Transformer.Pures.Register import Register


class PredicateWrite(Effect):

    def __init__(self, name, p_reg: Register, val: Pure):
        self.p_reg = p_reg
        self.val = val
        Effect.__init__(self, name, EffectType.SETG)

    def il_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """

        return f'write_pred({self.p_reg.get_name()}, {self.val.get_name()})'
