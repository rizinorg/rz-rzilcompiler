# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Hybrids.Hybrid import Hybrid, HybridType
from Transformer.PluginInfo import hexagon_c_call_prefix
from Transformer.Pures.Pure import ValueType


class Call(Hybrid):
    """ Class which is a call in the instruction semantics. Since the IL operation cannot model this with a branch
        to another function (this would be another IL op all together) it is modeled as a Hybrid op.
    """
    def __init__(self, name: str, val_type: ValueType, args: []):
        self.fcn_name = args[0]
        self.op_type = HybridType.CALL

        Hybrid.__init__(self, name, args[1:], val_type)

    def il_exec(self):
        def read_arg(arg) -> str:
            # Arguments can be strings
            return arg if isinstance(arg, str) else arg.il_read()
        return f'{hexagon_c_call_prefix + self.fcn_name.upper()}({", ".join([read_arg(arg) for arg in self.ops])})'

    def il_write(self):
        return self.il_exec()

    def il_read(self):
        # The value of the call is always stored in "ret_val"
        tmp = 'SIGNED(' if self.value_type.signed else 'UNSIGNED('
        tmp += f'{self.value_type.bit_width}'
        return f'{tmp}, VARL("ret_val"))'
