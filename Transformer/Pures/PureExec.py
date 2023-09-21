# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Exceptions import OverloadException
from rzil_compiler.Transformer.Pures.LetVar import LetVar, resolve_lets, get_local_pures
from rzil_compiler.Transformer.Pures.Pure import Pure, PureType, ValueType


class PureExec(Pure):
    """A class which describes Pure values which are the result of an operation.
    They difference to Pure, LocalVars and GlobalVars is only the initialization.
    """

    # If true, the code gets inlined (does not get it's own Pure variable initialized)
    inlined: bool = False

    def __init__(self, name: str, operands: [Pure], val_type: ValueType):
        """Pure operands must be ordered from left to right. None is not a valid value for an operand."""
        # Add LETs to a list for use during initialization.
        self.lets = get_local_pures(operands)
        self.ops = operands
        Pure.__init__(self, name, PureType.EXEC, val_type)

    def get_ops(self) -> list[Pure]:
        return self.ops

    def il_exec(self):
        """Returns the RZIL ops to execute the operation.
        :return: RZIL ops to exec the operation value.
        """
        raise OverloadException("")

    def il_init_var(self):
        if self.inlined:
            return ""
        if len(self.lets) == 0:
            init = f"RzILOpPure *{self.pure_var()} = {self.il_exec()};"
            return init
        init = f"RzILOpPure *{self.pure_var()} = "
        init += resolve_lets(self.ops, self) + ";"
        return init

    def il_read(self):
        self.reads += 1
        if self.inlined:
            return resolve_lets(self.ops, self)
        return self.pure_var()

    def vm_id(self, write_usage):
        return f'"{self.get_name()}"'
