# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Hybrids.Hybrid import PostfixExpr, Hybrid
from Transformer.Pures.GlobalVar import GlobalVar
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.Pure import ValueType, Pure


class PostfixIncDec(Hybrid):

    def __init__(self, name: str, operand: Pure, value_type: ValueType, hybrid_type: PostfixExpr):
        self.op_type = hybrid_type
        self.gl = get_scope_letter(operand)
        Hybrid.__init__(self, name, [operand], value_type)

    def il_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        name = self.ops[0].get_name()
        if self.op_type == PostfixExpr.INC or self.op_type == PostfixExpr.DEC:
            return f'SET{self.gl}("{name}", {self.il_exec()})'
        else:
            raise NotImplementedError(f'{self.op_type} not implemented.')

    def il_exec(self):
        if self.op_type == PostfixExpr.DEC:
            return f'DEC({self.il_read()})'
        elif self.op_type == PostfixExpr.INC:
            return f'INC({self.il_read()})'
        else:
            raise NotImplementedError(f'il_exec for {self.op_type} not implemented.')

    def il_read(self):
        """ Returns the RZIL ops to read the variable value.
        :return: RZIL ops to read the pure value.
        """
        return f'VAR{self.gl}("{self.ops[0].get_name()}")'


def get_scope_letter(op: Pure) -> str:
    if isinstance(op, GlobalVar):
        return 'G'
    elif isinstance(op, LocalVar):
        return 'L'
    else:
        raise NotImplementedError(f'No scoper letter given for {op}')
