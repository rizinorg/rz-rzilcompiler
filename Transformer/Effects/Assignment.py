# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Exceptions import OverloadException
from Transformer.Effect import Effect, EffectType
from Transformer.Pure import Pure, PureType
from enum import StrEnum

from Transformer.Pures.Add import Add


class AssignmentType(StrEnum):
    ASSIGN = '='
    ASSIGN_ADD = '+='
    ASSIGN_SUB = '-='
    ASSIGN_MUL = '*='
    ASSIGN_DIV = '/='
    ASSIGN_RIGHT = '>>='
    ASSIGN_LEFT = '<<='
    ASSIGN_MOD = '%='
    ASSIGN_AND = '&='
    ASSIGN_XOR = '^='
    ASSIGN_OR = '|='


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
            raise NotImplementedError('')
        self.set_dest()

    def set_dest(self):
        if self.assign_type == AssignmentType.ASSIGN:
            return
        elif self.assign_type == AssignmentType.ASSIGN_ADD:
            self.dest = Add(f'add{self.src.get_isa_name()}{self.dest.get_isa_name()}', self.src, self.dest)
        else:
            NotImplementedError('')

    def il_write(self):
        """ Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        if self.type == EffectType.SETG:
            return f'SETG({self.dest.get_assoc_name()}, {self.src.get_isa_name()})'
        elif self.type == EffectType.SETL:
            return f'SETG({self.dest.get_isa_name()}, {self.src.get_isa_name()})'
        else:
            raise NotImplementedError('')
