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
    SCALL = "sub_routine_call"
    SUB_ROUTINE = "sub_routine"


class HybridSeqOrder(Enum):
    SET_VAL_THEN_EXEC = auto()  # Constructs like i++
    EXEC_THEN_SET_VAL = auto()  # For normal sub_routines.
    EXEC_ONLY = auto()  # For sub_routines which return void.
    NOT_SET = auto()


class Hybrid(PureExec, Effect):
    seq_order: HybridSeqOrder = HybridSeqOrder.NOT_SET
    op_type: HybridType = None

    def __init__(self, name: str, operands: [Pure], value_type: ValueType):
        # Tracks the LocaLVars which reference this Hybrid.
        # If this set is empty the Hybrid is not used and can be removed.
        self.references_set = set()
        self.pure_init_count = 0
        self.effect_init_count = 0
        self.effect_ops = operands
        PureExec.__init__(self, name, operands, value_type)
        Effect.__init__(self, name, EffectType.SET)

    def il_init_var(self):
        if self.effect_init_count > 0:
            return ""
        self.effect_init_count += 1
        return Effect.il_init_var(self)

    def il_init_pure_var(self):
        if self.pure_init_count > 0:
            return ""
        self.pure_init_count += 1
        return Pure.il_init_var(self)

    def il_init_effect_var(self):
        if self.effect_init_count > 0:
            return ""
        self.effect_init_count += 1
        return Effect.il_init_var(self)

    def __str__(self):
        space = "_"
        if self.op_type in [HybridType.INC, HybridType.DEC]:
            space = ""
        return f"HYB({self.op_type}{space}{', '.join([str(op) for op in self.ops])})"
