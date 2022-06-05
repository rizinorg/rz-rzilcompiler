# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import Pure, PureType, ValueType


class LetVar(Pure):
    """ This class represents a LetVar. Let variables are immutable. """

    def __init__(self, name: str, value: int, value_type: ValueType):
        self.value = value
        super().__init__(name, PureType.LET, value_type)

    def get_val(self):
        """ Returns the value of the variable. """
        raise self.value

    def il_init_var(self):
        return f'RzILOpPure *{self.get_name()} = {self.value_type.il_op(self.value)};'

    def il_read(self):
        """ Returns the code to read the let variable for the VM. """
        return f'VARLP("{self.get_name()}")'
