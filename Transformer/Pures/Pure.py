# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum
from Exceptions import OverloadException


class PureType(Enum):
    GLOBAL = 0  # Registers
    LOCAL = 1  # Local variables
    LET = 2  # Let variables
    EXEC = 3  # Read memory access


class ValueType:
    def __init__(self, c_type: str, is_num: bool, bit_width: int):
        self.c_type = c_type
        self.is_num = is_num
        self.bit_width = bit_width


class Pure:
    name: str = ''  # Name of pure
    name_assoc: str = ''  # Name associated with the ISA name. E.g. ISA: "Rs" Associated: "R3"
    type: PureType = None
    value_type: ValueType = None

    def __init__(self, name: str, pure_type: PureType, value_type: ValueType):
        from Transformer.ILOpsHolder import ILOpsHolder

        holder = ILOpsHolder()
        if name in holder.read_ops or name in holder.exec_ops:
            return
        self.name = name
        self.name_assoc = name + '_assoc'
        self.type = pure_type
        self.value_type = value_type
        holder.add_pure(self)

    def get_name(self):
        """ Returns the name of the pure. If it is defined in the ISA, this returns teh ISA name. """
        return self.name

    def get_isa_name(self):
        """ Returns the name of the RzILOpPure variable. """
        return self.name

    def get_assoc_name(self):
        return self.name_assoc

    def set_value_type(self, value_type: ValueType):
        self.value_type = value_type

    def il_read(self):
        """ Returns the RZIL ops to read the variable value.
        :return: RZIL ops to read the pure value.
        """
        raise OverloadException('')

    def il_isa_to_assoc_name(self):
        """ Returns code to: Translate a placeholder ISA name of an operand (like u6:2 or Rs)
        to the real operand name of the current instruction.
        E.g. Rs -> "R3", u6 -> 0x3f
        """
        raise OverloadException('')

    def il_init_var(self):
        """ Initializes the global variable. Usually this means:
        1. Get real operand name from the instruction ("Rs" -> "R3")
        2. (if pure is read) Init a RzILOpPure variable.
        """
        raise OverloadException('')
