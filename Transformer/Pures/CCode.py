# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

#
# Any classes which produce no RZIL ops but C-code instead
#
from Transformer.PluginInfo import hexagon_c_call_prefix
from Transformer.Pures.Pure import ValueType, PureType
from Transformer.Pures.PureExec import PureExec


class CCall(PureExec):
    def __init__(self, name: str, val_type: ValueType, args: []):
        self.fcn_name = args[0]

        PureExec.__init__(self, name, args[1:], val_type)

    def il_exec(self):
        def read_arg(arg) -> str:
            # Arguments can be strings
            return arg if isinstance(arg, str) else arg.il_read()
        tmp = 'SIGNED(' if self.value_type.signed else 'UNSIGNED('
        tmp += f'{self.value_type.bit_width}'
        return f'{tmp}, {hexagon_c_call_prefix + self.fcn_name.upper()}({", ".join([read_arg(arg) for arg in self.ops])}))'
