# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from rzilcompiler.Transformer.Hybrids.Hybrid import Hybrid, HybridType, HybridSeqOrder
from rzilcompiler.Transformer.PluginInfo import hexagon_c_call_prefix
from rzilcompiler.Transformer.ValueType import ValueType, VTGroup
from rzilcompiler.Transformer.Pures.Register import Register
from rzilcompiler.Transformer.Pures.LetVar import LetVar, resolve_lets


class Call(Hybrid):
    """Class which is a call in the instruction semantics. Since the IL operation cannot model this with a branch
    to another function (this would be another IL op all together) it is modeled as a Hybrid op.
    """

    def __init__(self, name: str, val_type: ValueType, params: list):
        self.fcn_name = params[0]
        self.op_type = HybridType.CALL
        if val_type.group & VTGroup.VOID:
            self.seq_order = HybridSeqOrder.EXEC_ONLY
        else:
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
            return f"{hexagon_c_call_prefix + self.fcn_name.upper()}(pkt, hi->slot)"

        prefix = hexagon_c_call_prefix
        if self.fcn_name == "WRITE_REG":
            prefix = ""
        code = f'{prefix + self.fcn_name.upper()}({", ".join([read_param(param) for param in self.ops])})'
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
