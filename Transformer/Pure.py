# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum
from Exceptions import OverloadException


class PureType(Enum):
    GLOBAL = 0  # Registers
    LOCAL = 1  # Local variables
    EXEC = 2  # Any value returned from operations like add, sub etc.
    MEM = 3  # Read memory access


class Pure:
    name: str = ''  # Name of pure
    type: PureType = None

    def init(self, name: str, pure_type: PureType):
        self.name = name
        self.type = pure_type

    def get_name(self):
        return self.name

    def code_read(self):
        """ Returns the RZIL ops to read the variable value.
        :return: RZIL ops to read the pure value.
        """
        raise OverloadException('')

    def code_init_var(self):
        return f'RzIlOpPure *{self.name} = {self.code_read()};'
