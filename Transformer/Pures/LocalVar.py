# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid
from rzil_compiler.Exceptions import OverloadException
from rzil_compiler.Transformer.Pures.Pure import Pure, PureType
from rzil_compiler.Transformer.ValueType import ValueType, VTGroup


class LocalVar(Pure):
    """This class represents a LocalVar. It should not be confused with a LetVar!
    LocalVars do not get initialized like global vars. They are set when a value is assigned to them.
    """

    def __init__(
        self, name: str, value_type: ValueType, hybrid_owner: Hybrid | None = None
    ):
        if value_type and value_type.group & VTGroup.HYBRID_LVAR and not hybrid_owner:
            raise ValueError(
                "If this local var is a return value of a hybrid, the hybrid must be given as reference."
            )
        self.hybrid_owner = hybrid_owner
        Pure.__init__(self, name, PureType.LOCAL, value_type)

    def get_val(self):
        """Returns the value of the variable."""
        raise OverloadException("")

    def il_init_var(self) -> str:
        if self.value_type.group & VTGroup.HYBRID_LVAR:
            return ""  # Consumable return values of Hybrids don't get initialized. Only read.
        # Local vars are not initialized like global vars. They are initialized when an assignment to them happens.
        return f"// Declare: {self.value_type} {self.get_name()};"

    def il_read(self) -> str:
        """Returns the code to read the local variable for the VM."""
        self.reads += 1
        return f"VARL({self.vm_id()})"

    def vm_id(self) -> str:
        return f'"{self.get_name()}"'

    def __str__(self):
        return f"{self.get_name()}"
