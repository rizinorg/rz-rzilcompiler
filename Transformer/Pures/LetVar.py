# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import Pure, PureType, ValueType


class LetVar(Pure):
    """ This class represents a LetVar. Let variables are immutable. """

    def __init__(self, name: str, value: int, value_type: ValueType):
        self.value = value
        Pure.__init__(self, name, PureType.LET, value_type)

    def get_val(self):
        """ Returns the value of the variable. """
        return self.value

    def il_init_var(self):
        return f'RzILOpPure *{self.pure_var()} = {self.value_type.il_op(self.value)};'

    def il_read(self):
        """ Returns the code to read the let variable for the VM. """
        self.reads += 1
        return f'VARLP({self.vm_id(False)})'

    def vm_id(self, write_usage: bool):
        return f'"{self.get_name()}"'
