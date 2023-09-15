# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import Pure, PureType, ValueType


class LetVar(Pure):
    """This class represents a LetVar. Let variables are immutable."""

    def __init__(self, name: str, value: int, value_type: ValueType):
        self.value = value
        Pure.__init__(self, name, PureType.LET, value_type)

    def get_val(self):
        """Returns the value of the variable."""
        return self.value

    def il_init_var(self):
        return f"RzILOpPure *{self.pure_var()} = {self.value_type.il_op(self.value)};"

    def il_read(self):
        """Returns the code to read the let variable for the VM."""
        self.reads += 1
        return f"VARLP({self.vm_id(False)})"

    def vm_id(self, write_usage: bool):
        return f'"{self.get_name()}"'


def resolve_lets(lets: list[LetVar], consumer):
    """Wraps LET(...) around the consumer."""
    from Transformer.Pures.Number import Number
    from Transformer.Pures.PureExec import PureExec

    num_lets = len(lets) - sum(isinstance(l, Number) for l in lets)

    code = ""
    for let in lets:
        if isinstance(let, Number):
            # Numbers are initialized with UN()
            continue
        let_read = let.pure_var() if let.reads < 1 else f"DUP({let.pure_var()})"
        code += f"LET({let.vm_id(True)}, {let_read}, "
        let.reads += 1
    code += consumer.il_exec() if isinstance(consumer, PureExec) else consumer.il_read()
    code += ")" * num_lets
    return code
