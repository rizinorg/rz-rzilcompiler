# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Hybrids.Hybrid import HybridType, Hybrid, HybridSeqOrder
from Transformer.Pures.GlobalVar import GlobalVar
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.Pure import ValueType, Pure


class PostfixIncDec(Hybrid):
    def __init__(
        self, name: str, operand: Pure, value_type: ValueType, hybrid_type: HybridType
    ):
        self.op_type = hybrid_type
        self.gl = get_scope_letter(operand)
        self.seq_order = HybridSeqOrder.SET_VAL_THEN_EXEC

        Hybrid.__init__(self, name, [operand], value_type)

    def il_write(self):
        """Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        if self.op_type == HybridType.INC or self.op_type == HybridType.DEC:
            return f"SET{self.gl}({self.ops[0].vm_id(True)}, {self.il_exec()})"
        else:
            raise NotImplementedError(f"{self.op_type} not implemented.")

    def il_exec(self):
        if self.op_type == HybridType.DEC:
            return f"DEC({self.il_read()}, {self.value_type.bit_width})"
        elif self.op_type == HybridType.INC:
            return f"INC({self.il_read()}, {self.value_type.bit_width})"
        else:
            raise NotImplementedError(f"il_exec for {self.op_type} not implemented.")

    def il_read(self):
        """Returns the RZIL ops to read the variable value.
        :return: RZIL ops to read the pure value.
        """
        return self.ops[0].il_read()


def get_scope_letter(op: Pure) -> str:
    if isinstance(op, GlobalVar):
        return "G"
    elif isinstance(op, LocalVar):
        return "L"
    else:
        raise NotImplementedError(f"No scoper letter given for {op}")
