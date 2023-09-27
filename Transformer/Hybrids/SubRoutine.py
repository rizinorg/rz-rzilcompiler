# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import Enum

from rzil_compiler.Transformer.Pures.Parameter import Parameter
from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid, HybridType, HybridSeqOrder
from rzil_compiler.Transformer.PluginInfo import hexagon_c_call_prefix
from rzil_compiler.Transformer.Pures.Pure import ValueType


class SubRoutineInitType(Enum):
    DECL = 0
    DEF = 1
    CALL = 2


class SubRoutine(Hybrid):
    """
    Represents a sub routine.
    """

    def __init__(
        self, name: str, ret_type: ValueType, params: list[Parameter], body: str
    ):
        self.routine_name = name
        # Precompiled subroutine's body.
        self.body = "{\n" + body + "\n}"
        self.op_type = HybridType.SUB_ROUTINE
        self.seq_order = HybridSeqOrder.EXEC_THEN_SET_VAL

        Hybrid.__init__(self, name, params, ret_type)

    def il_init(self, sub_init_type=SubRoutineInitType.CALL) -> str:
        """
        Either as definition, declaration or call.
        Call is for initializations within another body statement and returns nothing.
        """
        if sub_init_type == SubRoutineInitType.CALL:
            return ""

        decl = (
            f"RZ_OWN RzILOpEffect *{hexagon_c_call_prefix.lower()}{self.routine_name}("
        )
        decl += ", ".join([p.get_rzi_decl() for p in self.ops])
        decl += ")"
        if sub_init_type == SubRoutineInitType.DECL:
            return decl
        decl += self.body
        return decl

    def il_write(self):
        raise ValueError("Sub-routines are immutable.")

    def il_exec(self):
        raise ValueError("A sub-routine cannot be executed. Only a SubRoutineCall can.")

    def il_read(self):
        # The value of the sub-routine is always stored in "ret_val"
        tmp = "SIGNED(" if self.value_type.signed else "UNSIGNED("
        tmp += (
            f"{self.value_type.bit_width}" if self.value_type.bit_width != 0 else "32"
        )
        return f'{tmp}, VARL("ret_val"))'


class SubRoutineCall(Hybrid):
    """
    Represents a call to a sub-routine.
    The operands passed to a SubRoutineCall are arguments instead of parameters.
    """
    def __init__(
        self, sub_routine: SubRoutine, args: list[Parameter]
    ):
        self.sub_routine = sub_routine
        self.seq_order = HybridSeqOrder.EXEC_THEN_SET_VAL

        Hybrid.__init__(self, sub_routine.get_name() + "_call", args, sub_routine.value_type)

    def il_exec(self):
        raise NotImplementedError()

    def il_init(self):
        raise NotImplementedError()

    def il_read(self):
        raise NotImplementedError()

    def il_write(self):
        raise ValueError("Sub-routines are immutable.")
