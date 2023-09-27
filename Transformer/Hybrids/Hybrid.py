# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import StrEnum, Enum

from rzil_compiler.Transformer.Effects.Effect import Effect, EffectType
from rzil_compiler.Transformer.Pures.Pure import ValueType, Pure
from rzil_compiler.Transformer.Pures.PureExec import PureExec


class HybridType(StrEnum):
    INC = "++"
    DEC = "--"
    CALL = "call"
    SUB_ROUTINE = "sub_routine"


class HybridSeqOrder(Enum):
    SET_VAL_THEN_EXEC = 0
    EXEC_THEN_SET_VAL = 1
    NOT_SET = 2


class Hybrid(PureExec, Effect):
    seq_order: HybridSeqOrder = HybridSeqOrder.NOT_SET

    def __init__(self, name: str, operands: [Pure], value_type: ValueType):
        self.effect_ops = operands
        PureExec.__init__(self, name, operands, value_type)
        Effect.__init__(self, name, EffectType.SET)

    def il_init_var(self):
        return Effect.il_init_var(self)
