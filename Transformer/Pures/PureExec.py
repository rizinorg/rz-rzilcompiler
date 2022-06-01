# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Exceptions import OverloadException
from Transformer.Pures.LetVar import LetVar
from Transformer.Pures.Pure import Pure, PureType, ValueType


class PureExec(Pure):
    """ A class which describes Pure values which are the result of an operation.
        They difference to Pure, LocalVars and GlobalVars is only the initialization.
    """

    def __init__(self, name: str, operands: [Pure]):
        """ Pure operands must be ordered from left to right. None is not a valid value for an operand.
        """
        # Add LETs to a list for use during initialization.
        self.lets = [op for op in operands if isinstance(op, LetVar)]
        self.ops = operands
        # Operand with the largest bit size determines the resulting value type of this operation.
        tmp_op: Pure = max(self.ops, key=lambda x: x.value_type.bit_width)
        super().__init__(name, PureType.EXEC, tmp_op.value_type)

    def il_exec(self):
        """ Returns the RZIL ops to execute the operation.
        :return: RZIL ops to exec the operation value.
        """
        raise OverloadException('')

    def il_init_var(self):
        init = f'RzIlOpPure *{self.get_name()} = {self.il_exec()});'
        return init
