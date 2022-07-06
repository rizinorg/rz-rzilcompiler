# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import StrEnum

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import ValueType, Pure
from Transformer.Pures.PureExec import PureExec


class PostfixExpr(StrEnum):
    INC = '++'
    DEC = '--'


class Hybrid(PureExec, Effect):

    def __init__(self, name: str, operands: [Pure], value_type: ValueType):
        PureExec.__init__(self, name, operands, value_type)
        Effect.__init__(self, name, EffectType.SET)

    def il_init_var(self):
        return Effect.il_init_var(self)
