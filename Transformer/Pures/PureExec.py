# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Exceptions import OverloadException
from Transformer.Pures.Pure import Pure, PureType, ValueType


class PureExec(Pure):
    """ A class which describes Pure values which are the result of an operation.
        They difference to Pure, LocalVars and GlobalVars is only the initialization.
    """

    def __init__(self, name: str, val_type: ValueType):
        super().__init__(name, PureType.EXEC, val_type)

    def il_exec(self):
        """ Returns the RZIL ops to execute the operation.
        :return: RZIL ops to exec the operation value.
        """
        raise OverloadException('')

    def il_init_var(self):
        init = f'RzIlOpPure *{self.get_name()} = {self.il_exec()});'
        return init
