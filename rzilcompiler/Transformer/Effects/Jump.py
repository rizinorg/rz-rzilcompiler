# SPDX-FileCopyrightText: 2022 Rot127 <rot127@posteo.com>
# SPDX-License-Identifier: LGPL-3.0-only
from rzilcompiler.Transformer.Hybrids.SubRoutine import SubRoutineCall
from rzilcompiler.Transformer.Effects.Effect import Effect, EffectType
from rzilcompiler.Transformer.Pures.Pure import Pure


class Jump(Effect):
    """
    Direct jump without setting C9 to the target address.
    """

    def __init__(self, name: str, target: Pure):
        self.target: Pure = target
        self.effect_ops = [self.target]
        Effect.__init__(self, name, EffectType.JUMP)

    def il_write(self):
        return f"SETL(bundle->jmp_flags[bundle->jmp_cnt], IL_TRUE)"

    def il_init_var(self) -> str:
        return (
            f"RzILOpEffect *{self.effect_var()} = {self.il_write()};\n"
            + "rz_return_val_if_fail(bundle->jmp_cnt < 2, NULL);\n"
            + f"bundle->jmp_set_addr[bundle->jmp_cnt] = SETL(bundle->jmp_targets[bundle->jmp_cnt], {self.target.il_read()});\n"
            + "bundle->jmp_cnt++;"
        )

    def __str__(self):
        return f"jump({self.target})"
