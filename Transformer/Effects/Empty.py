# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Effects.Effect import Effect, EffectType
from rzil_compiler.Transformer.Pures.Pure import Pure


class Empty(Effect):
    def __init__(self, name):
        self.effect_ops = []
        Effect.__init__(self, name, EffectType.EMPTY)

    def il_init_var(self) -> str:
        return ""

    def effect_var(self) -> str:
        """Returns the C variable name which holds the IL effect."""
        # No need to initialize it. We simply execute EMPTY()
        return self.il_write()

    def il_write(self):
        """Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """

        return "EMPTY()"

    def __str__(self):
        return "{}"
