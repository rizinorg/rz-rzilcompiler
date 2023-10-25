# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Pures.LetVar import LetVar
from rzil_compiler.Transformer.ValueType import ValueType, VTGroup


class Bool(LetVar):
    def __init__(self, name: str, val: bool):
        self.name = name
        v_type: ValueType = ValueType(False, 1, VTGroup.BOOL | VTGroup.PURE)
        LetVar.__init__(self, name, val, v_type)

    def il_init_var(self):
        if self.inlined:
            return ""
        return f"RzILOpBool *{self.pure_var()} = {'IL_TRUE' if self.get_val() else 'IL_FALSE'}"

    def il_read(self):
        return "IL_TRUE" if self.get_val() else "IL_FALSE"

    def __str__(self):
        return "TRUE" if self.get_val() else "FALSE"
