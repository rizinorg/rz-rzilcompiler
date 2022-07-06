# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum

from Transformer.Effects.Effect import Effect, EffectType
from Transformer.Pures.Pure import PureType, ValueType, Pure
from Transformer.Pures.PureExec import PureExec


class HybridOpType(Enum):
    INC = 0
    DEC = 1


class Hybrid(PureExec, Effect):

    def __init__(self, name: str, operands: list[Pure], value_type: ValueType):
        super().__init__(name, operands, value_type)
        super().__init__(name, EffectType.SETL)
