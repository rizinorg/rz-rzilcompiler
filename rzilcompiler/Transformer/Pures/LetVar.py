# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzilcompiler.Transformer.Pures.Pure import Pure, PureType
from rzilcompiler.Transformer.ValueType import ValueType


class LetVar(Pure):
    """This class represents a LetVar. Let variables are immutable."""

    # If true, the code gets inlined (does not get it's own Pure variable initialized)
    inlined: bool = False

    def __init__(self, name: str, value: int, value_type: ValueType):
        self.value = value
        Pure.__init__(self, name, PureType.LET, value_type)

    def get_val(self):
        """Returns the value of the variable."""
        return self.value

    def get_rzil_val(self) -> str:
        """Returns the value as UN(...)"""
        number = hex(self.get_val()) if self.get_val() > 31 else str(self.get_val())
        return f"{'SN' if self.value_type.signed else 'UN'}({self.value_type.bit_width}, {number})"

    def il_init_var(self):
        if self.inlined:
            return ""
        return f"RzILOpPure *{self.pure_var()} = {self.value_type.il_op(self.value)};"

    def il_read(self):
        """Returns the code to read the let variable for the VM."""
        self.reads += 1
        if self.inlined:
            return self.get_rzil_val()
        return f"VARLP({self.vm_id()})"

    def vm_id(self):
        return f'"{self.get_name()}"'


def get_local_pures(operands: list[Pure]) -> list[LetVar]:
    """Extracts a list of LetVars which were not initialized yet."""
    from rzilcompiler.Transformer.Pures.LocalVar import LocalVar
    from rzilcompiler.Transformer.Pures.PureExec import PureExec

    local_pures = list()

    if len(operands) == 0:
        return local_pures

    for op in operands:
        if isinstance(op, LocalVar):
            # LocalVars must be initialized and have their LocalPures
            # set there.
            continue
        if isinstance(op, PureExec):
            if not op.inlined:
                # Those ops were initialized as well and have the
                # LocalPures set there.
                continue
            # Search in the operands of the inline pure, for other LocalPures
            local_pures.extend(get_local_pures(op.ops))
            continue
        elif isinstance(op, LetVar):
            local_pures.append(op)
        else:
            continue
    return local_pures


def resolve_lets(operands: list[Pure], consumer) -> str:
    """Wraps LET(...) around the consumer for every LocalPure in the operands."""
    from rzilcompiler.Transformer.Pures.Number import Number
    from rzilcompiler.Transformer.Pures.PureExec import PureExec

    lets = get_local_pures(operands)
    if len(lets) == 0:
        return (
            consumer.il_exec() if isinstance(consumer, PureExec) else consumer.il_read()
        )

    num_lets = len(lets) - len([l for l in lets if l.inlined])
    code = ""
    for let in [l for l in lets if not l.inlined]:
        let_read = let.pure_var() if let.reads < 1 else f"DUP({let.pure_var()})"
        code += f"LET({let.vm_id()}, {let_read}, "
        let.reads += 1
    code += consumer.il_exec() if isinstance(consumer, PureExec) else consumer.il_read()
    code += ")" * num_lets
    return code
