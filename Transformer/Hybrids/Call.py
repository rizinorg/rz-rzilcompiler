# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from rzil_compiler.HexagonExtensions import get_fcn_arg_types
from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid, HybridType, HybridSeqOrder
from rzil_compiler.Transformer.PluginInfo import hexagon_c_call_prefix
from rzil_compiler.Transformer.Pures.Cast import Cast
from rzil_compiler.Transformer.Pures.Pure import ValueType
from rzil_compiler.Transformer.Pures.Register import Register
from rzil_compiler.Transformer.Pures.LetVar import LetVar, resolve_lets


class Call(Hybrid):
    """Class which is a call in the instruction semantics. Since the IL operation cannot model this with a branch
    to another function (this would be another IL op all together) it is modeled as a Hybrid op.
    """

    def __init__(self, name: str, val_type: ValueType, args: []):
        self.fcn_name = args[0]
        self.op_type = HybridType.CALL
        self.seq_order = HybridSeqOrder.EXEC_THEN_SET_VAL

        Hybrid.__init__(self, name, args[1:], val_type)
        arg_types = get_fcn_arg_types(self.fcn_name)
        if len(self.ops) != len(arg_types):
            raise NotImplementedError("Not all ops have a type assigned.")
        for i, (arg, a_type) in enumerate(zip(self.ops, arg_types)):
            if isinstance(arg, str):
                continue
            if not a_type or arg.value_type == a_type:
                continue

            self.ops[i] = Cast(f"arg_cast", a_type, arg)

    def il_exec(self):
        def read_arg(arg) -> str:
            # Arguments can be strings like enums
            if isinstance(arg, str):
                return arg

            if isinstance(arg, LetVar):
                return resolve_lets([arg], arg)
            elif isinstance(arg, Register) and arg.get_name()[0] == "P":
                return f'"{arg.get_name()}"'
            return arg.il_read()

        code = f'{hexagon_c_call_prefix + self.fcn_name.upper()}({", ".join([read_arg(arg) for arg in self.ops])})'
        return code

    def il_write(self):
        return self.il_exec()

    def il_read(self):
        # The value of the call is always stored in "ret_val"
        tmp = "SIGNED(" if self.value_type.signed else "UNSIGNED("
        tmp += (
            f"{self.value_type.bit_width}" if self.value_type.bit_width != 0 else "32"
        )
        return f'{tmp}, VARL("ret_val"))'
