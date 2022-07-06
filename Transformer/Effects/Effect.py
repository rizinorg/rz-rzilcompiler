# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum
from Exceptions import OverloadException


class EffectType(Enum):
    SETG = 0
    SETL = 1
    STOREW = 2
    STORE = 3
    JUMP = 4
    NOP = 5
    LOOP = 6


class Effect:
    name: str = ''
    type: EffectType = None

    def __init__(self, name: str, effect_type: EffectType):
        from Transformer.ILOpsHolder import ILOpsHolder

        self.name = name
        self.type = effect_type

        holder = ILOpsHolder()
        if name in holder.write_ops:
            return
        holder.add_effect(self)

    def get_name(self):
        return self.name

    def il_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        raise OverloadException('')

    def il_init_var(self):
        return f'RzIlOpEffect *{self.get_name()} = {self.il_write()};'
