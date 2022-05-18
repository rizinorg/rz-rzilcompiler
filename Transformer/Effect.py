# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum
from Exceptions import OverloadException


class EffectType(Enum):
    SETG = 0
    SETL = 1
    STOREW = 2
    STORE = 3


class Effect:
    name: str = ''
    type: EffectType = None

    def init(self, name: str, effect_type: EffectType):
        self.name = name
        self.type = effect_type

    def get_name(self):
        return self.name

    def get_isa_name(self):
        """ Returns the name of the RzILOpPure variable. """
        return self.name

    def code_get_vm_name(self):
        """ Returns the name by which the VM knows this variable. """
        return self.name

    def code_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        raise OverloadException('')

    def code_init_var(self):
        return f'RzIlOpEffect *{self.get_isa_name()} = {self.code_write()};'
