# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Hybrids.SubRoutine import build_arg_list
from rzil_compiler.Transformer.Pures.PureExec import PureExec
from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.ValueType import ValueType


class Macro:
    def __init__(
        self,
        name: str,
        ret_type: ValueType,
        param_types: list[ValueType],
        rzil_macro: str,
    ):
        self.name = name
        self.qemu_name = name
        self.return_type = ret_type
        self.param_types = param_types
        self.rzil_macro = rzil_macro

    def get_rzil_name(self):
        return self.rzil_macro


class MacroInvocation(PureExec):
    """
    A Macro which maps either to a RZIL function directly or some more complex function.
    So the implementation is not the concern of this compiler.
    It is always inlined. It only exists to do proper type checking.
    """

    def __init__(self, name: str, arguments: list[Pure], macro: Macro):
        self.inlined: bool = True
        self.macro = macro
        self.rzil_macro = macro.rzil_macro
        if self.macro.qemu_name == "fFLOAT":
            arguments = ["RZ_FLOAT_IEEE754_BIN_32"] + arguments
        elif self.macro.qemu_name == "fDOUBLE":
            arguments = ["RZ_FLOAT_IEEE754_BIN_64"] + arguments

        PureExec.__init__(self, name, arguments, macro.return_type)

    def il_exec(self):
        code = (
            f"{self.macro.get_rzil_name()}("
            f"{build_arg_list(self.ops, self.macro.param_types)}"
            ")"
        )
        return code

    def il_init_var(self):
        return ""

    def __str__(self):
        return f"{self.macro.name}({', '.join(str(op) for op in self.ops)})"
