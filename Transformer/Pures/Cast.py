# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.ValueType import ValueType
from rzil_compiler.Transformer.Pures.PureExec import PureExec


class Cast(PureExec):
    def __init__(self, name: str, type_specifier: ValueType, val: Pure):
        PureExec.__init__(self, name, [val], type_specifier)

    def il_exec(self) -> str:
        if self.value_type.signed:
            fill_bit = f"MSB("
            if hasattr(self.ops[0], "inlined") and not self.ops[0].inlined:
                fill_bit += f"DUP({self.ops[0].il_read()}))"
            else:
                fill_bit += f"{self.ops[0].il_read()})"
        else:
            fill_bit = "IL_FALSE"
        return f"CAST({self.value_type.bit_width}, {fill_bit}, {self.ops[0].il_read()})"
