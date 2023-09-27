# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from rzil_compiler.Transformer.Pures.Pure import Pure, PureType
from rzil_compiler.Transformer.ValueType import ValueType, get_value_type_by_c_type


class Parameter(Pure):
    """
    This class represents a parameter of a sub-routine.
    It is in general treated immutable, never initialized and only referenced by its name.
    """

    def __init__(self, name: str, value_type: ValueType):
        Pure.__init__(self, name, PureType.LET, value_type)

    def get_val(self):
        raise ValueError("Parameters have no explicit value.")

    def get_rzil_val(self) -> str:
        """Returns the value as the name of the variable holding the Pure."""
        return self.get_name()

    def il_init_var(self):
        raise ValueError("Parameters should not be initialized!")

    def il_read(self):
        """Returns the code to read the let variable for the VM."""
        self.reads += 1
        return self.get_rzil_val()

    def vm_id(self, write_usage: bool):
        return self.get_rzil_val()

    def get_rzi_decl(self):
        return f"RZ_BORROW RzILOpPure *{self.get_name()}"


def get_parameter_by_decl(decl: str) -> Parameter:
    """
    Returns a Parameter object as defined in the declaration string.

    :param decl: The declaration of the for "<c_type> <id>"
    :return: And initialized Parameter object with the type and name of the declaration.
    """
    ptype, name = decl.split(" ")
    return Parameter(name, get_value_type_by_c_type(ptype))
