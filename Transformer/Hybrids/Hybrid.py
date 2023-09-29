# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import StrEnum, Enum, auto

from rzil_compiler.Transformer.Effects.Effect import Effect, EffectType
from rzil_compiler.Transformer.Pures.Pure import Pure
from rzil_compiler.Transformer.ValueType import ValueType
from rzil_compiler.Transformer.Pures.PureExec import PureExec


class HybridType(StrEnum):
    INC = "++"
    DEC = "--"
    CALL = "call"
    SUB_ROUTINE = "sub_routine"


class HybridSeqOrder(Enum):
    SET_VAL_THEN_EXEC = auto()  # Constructs like i++
    EXEC_THEN_SET_VAL = auto()  # For normal sub_routines.
    EXEC_ONLY = auto()  # For sub_routines which return void.
    NOT_SET = auto()


class Hybrid(PureExec, Effect):
    seq_order: HybridSeqOrder = HybridSeqOrder.NOT_SET

    def __init__(self, name: str, operands: [Pure], value_type: ValueType):
        self.effect_ops = operands
        PureExec.__init__(self, name, operands, value_type)
        Effect.__init__(self, name, EffectType.SET)

    def il_init_var(self):
        return Effect.il_init_var(self)
