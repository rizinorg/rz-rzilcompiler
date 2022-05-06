# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Exceptions import OverloadException
from Transformer.Effect import Effect, EffectType
from Transformer.Pure import Pure, PureType
from enum import Enum


class AssignmentType(Enum):
    ASGN = '='
    ASGN_ADD = '+='
    ASGN_SUB = '-='
    ASGN_MUL = '*='
    ASGN_DIV = '/='


class Assignment(Effect):
    name = ''
    type = None
    dest = None
    src = None

    def __init__(self, name: str, assign_type: AssignmentType, dest: Pure, src: Pure):
        self.assign_type = assign_type
        self.dest = dest
        self.src = src

        if dest.type == PureType.LOCAL:
            super().init(name, EffectType.SETL)
        elif dest.type == PureType.GLOBAL:
            super().init(name, EffectType.SETG)
        else:
            raise NotImplementedError()

    def get_isa_name(self):
        """ Returns the name of the RzILOpPure variable. """
        return self.name

    def code_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        if self.type == EffectType.SETG:
            return f'SETG("{self.dest.get_isa_name()}", {self.src.get_isa_name()})'
        else:
            raise NotImplementedError()
