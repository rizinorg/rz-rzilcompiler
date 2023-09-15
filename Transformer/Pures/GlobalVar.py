# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Pures.Pure import Pure, PureType, ValueType


class GlobalVar(Pure):
    def __init__(self, name: str, v_type: ValueType):
        Pure.__init__(self, name, PureType.GLOBAL, v_type)

    def il_read(self):
        if self.reads < 1:  # First use of this variable
            ret = self.pure_var()
        else:
            ret = f"DUP({self.pure_var()})"

        self.reads += 1
        return ret
