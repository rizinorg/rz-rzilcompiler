# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Exceptions import OverloadException
from rzil_compiler.Transformer.Pures.Pure import Pure, PureType, ValueType


class LocalVar(Pure):
    """This class represents a LocalVar. It should not be confused with a LetVar!
    LocalVars do not get initialized like global vars. They are set when a value is assigned to them.
    """

    def __init__(self, name: str, value_type: ValueType):
        Pure.__init__(self, name, PureType.LOCAL, value_type)

    def get_val(self):
        """Returns the value of the variable."""
        raise OverloadException("")

    def il_init_var(self) -> str:
        # Local vars are not initialized like global vars. They are initialized when an assignment to them happens.
        return f"// Declare: {self.value_type} {self.get_name()};"

    def il_read(self) -> str:
        """Returns the code to read the local variable for the VM."""
        self.reads += 1
        return f"VARL({self.vm_id(False)})"

    def vm_id(self, write_usage: bool) -> str:
        return f'"{self.get_name()}"'
