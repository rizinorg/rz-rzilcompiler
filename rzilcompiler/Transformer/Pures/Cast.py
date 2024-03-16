# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzilcompiler.Transformer.Pures.Pure import Pure
from rzilcompiler.Transformer.ValueType import ValueType
from rzilcompiler.Transformer.Pures.PureExec import PureExec


class Cast(PureExec):
    def __init__(self, name: str, type_specifier: ValueType, val: Pure):
        PureExec.__init__(self, name, [val], type_specifier)

    def il_exec(self) -> str:
        if self.value_type.signed and self.ops[0].value_type.signed:
            fill_bit = f"MSB({self.ops[0].il_read()})"
        else:
            fill_bit = "IL_FALSE"
        return f"CAST({self.value_type.bit_width}, {fill_bit}, {self.ops[0].il_read()})"

    def __str__(self):
        return f"(({self.value_type}) {self.ops[0]})"
