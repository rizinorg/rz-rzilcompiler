# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import Pure, PureType, ValueType


class GlobalVar(Pure):
    reads = None

    def __init__(self, name: str, v_type: ValueType):
        self.reads = 0
        Pure.__init__(self, name, PureType.GLOBAL, v_type)

    def il_read(self):
        if self.reads < 1:  # First use of this variable
            ret = self.pure_var()
        else:
            ret = f'DUP({self.pure_var()})'

        self.reads += 1
        return ret

    def vm_id(self, write_usage: bool):
        # Global var names (registers mainly) are stored in "<reg>_assoc" variables.
        if write_usage:
            return self.get_assoc_name(True)
