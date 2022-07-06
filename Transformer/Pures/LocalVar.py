# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Exceptions import OverloadException
from Transformer.Pures.Pure import Pure, PureType, ValueType


class LocalVar(Pure):
    """ This class represents a LocalVar. It should not be confused with a LetVar!
        LocalVars do not get initialized like global vars. They are set when a value is assigned to them.
    """

    def __init__(self, name: str, value_type: ValueType):
        Pure.__init__(self, name, PureType.LOCAL, value_type)

    def get_val(self):
        """ Returns the value of the variable. """
        raise OverloadException('')

    def il_init_var(self):
        # Local vars are not initialized like global vars. They are initialized when an assignment to them happens.
        return f'// Declare: {self.value_type} {self.get_isa_name()};'

    def il_read(self):
        """ Returns the code to read the local variable for the VM. """
        return f'VARL("{self.get_name()}")'
