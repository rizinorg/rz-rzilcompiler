# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum

from rzil_compiler.Transformer.ValueType import ValueType
from rzil_compiler.Exceptions import OverloadException


class PureType(Enum):
    GLOBAL = 0  # Registers
    LOCAL = 1  # Local variables
    LET = 2  # Let variables
    EXEC = 3  # Read memory access, math ops etc.
    C_CODE = 4  # Anything Pure returned by a C code call


class Pure:
    name: str = ""  # Name of pure
    isa_name = None
    type: PureType = None
    value_type: ValueType = None
    num_id = -1

    def __init__(self, name: str, pure_type: PureType, value_type: ValueType):
        self.reads: int = 0
        self.name = name
        self.type = pure_type
        self.value_type = value_type

    def set_num_id(self, num_id: int):
        self.num_id = num_id

    def set_name(self, name: str):
        self.name = name

    def get_name(self) -> str:
        """Returns the name of the pure. If it is defined in the ISA, this returns the ISA name."""
        return self.isa_name if self.isa_name else self.name

    def set_isa_name(self, isa_name: str):
        self.isa_name = isa_name

    def get_isa_name(self) -> str:
        """Returns the name of the RzILOpPure variable as in the ISA manual."""
        return self.isa_name

    def pure_var(self) -> str:
        """Returns the C variable name which holds the IL Pure."""
        return self.get_name()

    def vm_id(self) -> str:
        """
        Returns the id this Pure is known to the VM as string or a variable name which holds it.
        """
        raise OverloadException("")

    def set_value_type(self, value_type: ValueType) -> None:
        self.value_type = value_type

    def il_read(self) -> str:
        """Returns the RZIL ops to read the variable value.
        :return: RZIL ops to read the pure value.
        """
        raise OverloadException("")

    def il_init_var(self) -> str:
        """Initializes the global variable. Usually this means:
        1. Get real operand name from the instruction ("Rs" -> "R3")
        2. (if pure is read) Init a RzILOpPure variable.
        """
        raise OverloadException("")
