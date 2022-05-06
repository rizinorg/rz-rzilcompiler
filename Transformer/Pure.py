# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum
from Exceptions import OverloadException
from itertools import count

class PureType(Enum):
    GLOBAL = 0  # Registers
    LOCAL = 1  # Local variables
    EXEC = 2  # Any value returned from operations like add, sub etc.
    MEM = 3  # Read memory access


class Pure:
    name: str = ''  # Name of pure
    name_assoc: str = '' # Name associated with the ISA name. E.g. ISA: "Rs" Associated: "R3"
    type: PureType = None
    _ids = count(0)

    def init(self, name: str, pure_type: PureType):
        self.name = name
        self.name_assoc = name + '_assoc'
        self.type = pure_type
        self.id = next(self._ids)

    def get_name(self):
        return self.name

    def get_isa_name(self):
        """ Returns the name of the RzILOpPure variable. """
        return self.name

    def get_assoc_name(self):
        return self.name_assoc

    def code_read(self):
        """ Returns the RZIL ops to read the variable value.
        :return: RZIL ops to read the pure value.
        """
        raise OverloadException('')
    
    def code_isa_to_assoc_name(self):
        """ Returns code to: Translate a placeholder ISA name of an operand (like u6:2 or Rs)
        to the real operand name of the current instruction.
        E.g. Rs -> "R3", u6 -> 0x3f
        """
        raise OverloadException('')

    def code_init_var(self):
        """ Initializes the global variable. Usually this means:
        1. Get real operand name from the instruction ("Rs" -> "R3")
        2. (if pure is read) Init a RzILOpPure variable.
        """
        raise OverloadException('')
        