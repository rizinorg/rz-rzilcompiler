# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import Pure


class Jump(Effect):
    def __init__(self, name: str, target: Pure):
        self.target = target
        self.effect_ops = [self.target]
        Effect.__init__(self, name, EffectType.JUMP)

    def il_write(self):
        """Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """

        return f"JMP({self.target.il_read()})"
