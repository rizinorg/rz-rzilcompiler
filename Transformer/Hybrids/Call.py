# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid, HybridType, HybridSeqOrder
from rzil_compiler.Transformer.PluginInfo import hexagon_c_call_prefix
from rzil_compiler.Transformer.Pures.Pure import ValueType
from rzil_compiler.Transformer.Pures.Register import Register
from rzil_compiler.Transformer.Pures.LetVar import LetVar, resolve_lets


class Call(Hybrid):
    """Class which is a call in the instruction semantics. Since the IL operation cannot model this with a branch
    to another function (this would be another IL op all together) it is modeled as a Hybrid op.
    """

    def __init__(self, name: str, val_type: ValueType, params: list):
        self.fcn_name = params[0]
        self.op_type = HybridType.CALL
        self.seq_order = HybridSeqOrder.EXEC_THEN_SET_VAL

        Hybrid.__init__(self, name, params[1:], val_type)

    def il_exec(self):
        def read_param(param) -> str:
            # Arguments can be strings like enums
            if isinstance(param, str):
                return param

            if isinstance(param, LetVar):
                return resolve_lets([param], param)
            elif isinstance(param, Register) and param.get_name()[0] == "P":
                return f'"{param.get_name()}"'
            return param.il_read()

        if self.fcn_name.upper() == "STORE_SLOT_CANCELLED":
            return f"{hexagon_c_call_prefix + self.fcn_name.upper()}(insn->slot)"
        elif self.fcn_name.upper() == "FCIRC_ADD":
            # For those we need to pass the name of the tmp register as well.
            in_out_reg = self.ops[0]
            while not isinstance(in_out_reg, Register):
                # We might have to skip Casts
                in_out_reg = in_out_reg.ops[0]

            code = (
                f"{hexagon_c_call_prefix + self.fcn_name.upper()}("
                f"{in_out_reg.get_assoc_name(write_usage=True)}, "  # input/output register
                f'{", ".join([read_param(param) for param in self.ops])})'
            )
            return code

        code = f'{hexagon_c_call_prefix + self.fcn_name.upper()}({", ".join([read_param(param) for param in self.ops])})'
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
