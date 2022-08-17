# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.Pure import ValueType


class Variable(LocalVar):
    """ This class represents a C variable.
    """

    def __init__(self, name: str, val_type: ValueType):
        # Value type is set on assignment.
        LocalVar.__init__(self, name, value_type=val_type)

    def il_init_var(self):
        # Local vars are not initialized like global vars. They are initialized when an assignment to them happens.
        code = f'// Declare: {self.value_type} {self.get_name()};\n'
        code += f'RzILOpPure *{self.pure_var()} = {self.il_read()};'
        return code
