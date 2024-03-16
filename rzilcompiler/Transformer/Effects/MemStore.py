# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzilcompiler.Transformer.Effects.Effect import Effect, EffectType
from rzilcompiler.Transformer.Pures.Pure import Pure


class MemStore(Effect):
    def __init__(self, name: str, va: Pure, data_var: Pure):
        self.va = va
        self.data_var = data_var
        self.effect_ops = [self.va, self.data_var]
        Effect.__init__(self, name, EffectType.STOREW)

    def il_write(self):
        """Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """

        return f"STOREW({self.va.il_read()}, {self.data_var.il_read()})"

    def __str__(self):
        return f"mem_store_{self.data_var.value_type}({self.va}, {self.data_var})"
