# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from rzil_compiler.Transformer.Hybrids.SubRoutine import SubRoutineCall
from rzil_compiler.Transformer.Effects.Effect import Effect, EffectType
from rzil_compiler.Transformer.Pures.Pure import Pure


class Jump(Effect):
    """
    Direct jump without setting C9 to the target address.
    If the C9 should be set before, use the set_c9_jump subroutine instead.
    """

    def __init__(self, name: str, target: Pure):
        self.target: Pure = target
        self.effect_ops = [self.target]
        Effect.__init__(self, name, EffectType.JUMP)

    def il_write(self):
        return f'SEQ2(SETL("jump_flag", IL_TRUE), JMP({self.target.il_read()}))'
