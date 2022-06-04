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
    """ Is used to match value against their UN() and SN() equivalence. """
    def __init__(self, signed: bool, bit_width: int):
        self.signed = signed
        self.bit_width = bit_width

    def il_op(self, value: int):
        """ Returns the corresponding SN/UN(size, val) string. """
        s = 'SN' if self.signed else 'UN'
        s += f'({self.bit_width}, {value})'
        return s

    def __eq__(self, other):
        return (self.bit_width == other.bit_width) and (self.signed == other.signed)


class Pure:
    name: str = ''  # Name of pure
    isa_name = None
    name_assoc: str = ''  # Name associated with the ISA name. E.g. ISA: "Rs" Associated: "R3"
    type: PureType = None
    value_type: ValueType = None

    def __init__(self, name: str, pure_type: PureType, value_type: ValueType):
        from Transformer.ILOpsHolder import ILOpsHolder

        self.name = name
        self.name_assoc = name + '_assoc'
        self.type = pure_type
        self.value_type = value_type

        holder = ILOpsHolder()
        if name in holder.read_ops or name in holder.exec_ops:
            return
        holder.add_pure(self)

    def get_name(self):
        """ Returns the name of the pure. If it is defined in the ISA, this returns the ISA name. """
        return self.isa_name if self.isa_name else self.name

    def set_isa_name(self, isa_name: str):
        self.isa_name = isa_name

    def get_isa_name(self):
        """ Returns the name of the RzILOpPure variable as in the ISA manual. """
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
