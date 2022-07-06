# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import Pure


class ForLoop(Effect):

    """
    for (init ; control ; after_cycle) { compound }
    """

    def __init__(self, name: str, init: Effect, control: Pure, after_cycle: Effect, compound: list[Effect]):
        self.init = init  # declaration/assignment
        self.control = control  # Condition
        self.after = after_cycle  # After loop expression
        self.compound = compound
        Effect.__init__(self, name, EffectType.LOOP)

    def il_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """

        return f'SEQ2({self.init.il_write()},\n' \
               f'REPEAT({self.control.il_read()},\n' \
               f'SEQN({", ".join([effect.il_write() for effect in self.compound + [self.after]])})))'
