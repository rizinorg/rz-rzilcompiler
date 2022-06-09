# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

#
# Any classes which produce no RZIL ops but C-code instead
#

from Transformer.Pures.Pure import Pure, ValueType, PureType


class CCall(Pure):
    def __init__(self, name: str, val_type: ValueType, args: []):
        self.args = args
        self.fcn_name = args[0]

        super().__init__(name, PureType.C_CODE, val_type)

    def il_read(self):
        def read_arg(arg):
            # Arguments can be strings
            return arg if isinstance(arg, str) else arg.il_read()

        return f'{self.fcn_name}({", ".join([read_arg(arg) for arg in self.args[1:]])})'
