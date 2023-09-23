# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.Effects.Effect import Effect, EffectType
from rzil_compiler.Transformer.Pures.LetVar import LetVar, resolve_lets
from rzil_compiler.Transformer.Pures.Pure import Pure, PureType
from enum import StrEnum

from rzil_compiler.Transformer.Pures.Register import Register


class AssignmentType(StrEnum):
    ASSIGN = "="
    ASSIGN_ADD = "+="
    ASSIGN_SUB = "-="
    ASSIGN_MUL = "*="
    ASSIGN_DIV = "/="
    ASSIGN_RIGHT = ">>="
    ASSIGN_LEFT = "<<="
    ASSIGN_MOD = "%="
    ASSIGN_AND = "&="
    ASSIGN_XOR = "^="
    ASSIGN_OR = "|="


class Assignment(Effect):
    name = ""
    type = None
    dest = None
    src = None

    def __init__(self, name: str, assign_type: AssignmentType, dest: Pure, src: Pure):
        self.assign_type = assign_type
        self.dest = dest
        self.src = src
        self.effect_ops = [self.dest, self.src]

        if dest.type == PureType.LOCAL:
            Effect.__init__(self, name, EffectType.SETL)
        elif dest.type == PureType.GLOBAL:
            Effect.__init__(self, name, EffectType.SETG)
        else:
            raise NotImplementedError(f"Dest type {self.dest.type} not handled.")
        if isinstance(self.dest, Register):
            self.dest.add_write_property()

    def il_write(self):
        """Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        from rzil_compiler.Transformer.Pures.Immediate import Immediate

        if isinstance(self.src, Immediate):
            self.src.assign_usage = True
            read = self.src.il_read()
        else:
            read = self.src.il_read()
        if self.type == EffectType.SETG and isinstance(self.dest, Register):
            if self.dest.is_explicit or self.dest.is_reg_alias:
                return f"WRITE_REG(pkt, &{self.dest.vm_id(True)}, {read})"
            return f"WRITE_REG(pkt, {self.dest.vm_id(True)}, {read})"
        elif self.type == EffectType.SETL:
            return f"SETL({self.dest.vm_id(True)}, {read})"
        else:
            raise NotImplementedError(
                f"Effect type {self.type} and to {self.dest} not handled."
            )
