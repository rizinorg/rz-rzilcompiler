# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import re
from enum import Enum

from rzil_compiler.Exceptions import OverloadException
from rzil_compiler.Transformer.Pures.Parameter import Parameter
from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid, HybridType, HybridSeqOrder
from rzil_compiler.Transformer.PluginInfo import hexagon_c_call_prefix
from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.ValueType import ValueType, VTGroup


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
        self.body = self.check_for_bundle_usage(body)
        self.op_type = HybridType.SUB_ROUTINE
        self.seq_order = HybridSeqOrder.EXEC_THEN_SET_VAL

        Hybrid.__init__(self, name, params, ret_type)

    def check_for_bundle_usage(self, code: str) -> str:
        if re.search(r"\Wpkt\W", code):
            code = "HexPkt *pkt = bundle->pkt;\n" + code
        if re.search(r"\Whi\W", code):
            code = "const HexInsn *hi = bundle->insn;\n" + code
        return " {\n" + code + "\n}"

    def get_parameter_value_types(self) -> list[ValueType]:
        """Returns the parameter value types as ordered list (left to right)."""
        return [p.value_type for p in self.ops]

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
        raise OverloadException(
            "Must be overloaded with the knowledge about args used."
        )

    def il_exec(self):
        return ""

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

    def __init__(self, sub_routine: SubRoutine, args: list[Pure]):
        self.inlined = True  # Calls are always inlined.
        self.sub_routine = sub_routine
        self.args: list[Pure] = args
        self.seq_order = HybridSeqOrder.EXEC_THEN_SET_VAL

        Hybrid.__init__(
            self, sub_routine.get_name() + "_call", args, sub_routine.value_type
        )

    def il_exec(self):
        return ""

    def il_init(self):
        """No initialization needed."""
        return ""

    def il_read(self):
        return self.sub_routine.il_read()

    def il_write(self):
        code = f"{hexagon_c_call_prefix.lower() + self.sub_routine.get_name()}("
        for i, (arg, ptype) in enumerate(zip(self.args, self.sub_routine.get_parameter_value_types())):
            if i > 0:
                code += ", "
            if ptype.group & VTGroup.EXTERNAL:
                # Parameter passed from outer scope
                if isinstance(arg, Parameter):
                    code += arg.get_name()
                    continue
                # We pass the argument as external type. So the operand of the variable is passed.
                # This operand should have the external type.
                if "get_op_var" not in dir(arg):
                    raise ValueError(f"{arg} as no method to get it's operand holding variable name.")
                code += arg.get_op_var()
            elif ptype.group & VTGroup.PURE:
                # Normal pure.
                code += arg.il_read()
            else:
                raise ValueError(f"{arg.group} not handled to initialize a sub-routine arguments.")
        code += ")"
        return code
