# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from Transformer.Effects.Assignment import Assignment, AssignmentType
from Transformer.ILOpsHolder import OpCounter
from Transformer.PluginInfo import isa_to_imm_fnc, isa_to_imm_args
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.Pure import ValueType


class Immediate(LocalVar):
    def __init__(self, name: str, v_type: ValueType):
        self.name = name
        self.v_type = v_type
        LocalVar.__init__(self, name, value_type=v_type)
        self.set_isa_name(name)

    def il_init_var(self, isa_to_imm_fcn=None):
        sign = 's' if self.v_type.signed else 'u'
        il_macro = f'{sign.upper()}N'
        width = self.v_type.bit_width
        cast = f'({sign}t{width if width > 8 else 8})'
        get_imm = f'{isa_to_imm_fnc}({", ".join(isa_to_imm_args)}, \'{self.get_isa_name()}\''
        return f'RzILOpPure *{self.pure_var()} = {il_macro}({width}, {cast} {get_imm}));'
