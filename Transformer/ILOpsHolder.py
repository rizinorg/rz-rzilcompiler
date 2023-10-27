# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from rzil_compiler.Transformer.Effects.Sequence import Sequence
from rzil_compiler.Transformer.ValueType import VTGroup
from rzil_compiler.Transformer.Effects.Effect import Effect
from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid
from rzil_compiler.Transformer.Pures.Pure import Pure, PureType


class ILOpsHolder:
    def __init__(self):
        # Total count of hybrids seen during transformation
        self.hybrid_op_count = 0
        self.hybrid_effect_dict: dict[str:Sequence] = dict()
        self.read_ops: dict = dict()
        self.exec_ops: dict = dict()
        self.write_ops: dict = dict()
        self.let_ops: dict = dict()  # immutable LET vars.
        self.op_count = 0

    def get_op_count(self):
        cnt = self.op_count
        self.op_count += 1
        return cnt

    def add_op(self, op):
        """
        Adds an IL operation and appends an id to its
        name to make the name unique.
        """
        if isinstance(op, Hybrid):
            self.add_hybrid(op)
        elif isinstance(op, Pure):
            self.add_pure(op)
        elif isinstance(op, Effect):
            self.add_effect(op)
        else:
            raise NotImplementedError(
                f"Can not add op {op} because it has no op holder list."
            )

    def add_pure(self, pure: Pure):
        if pure.type == PureType.GLOBAL or pure.type == PureType.LOCAL:
            self.read_ops[pure.get_name()] = pure
        elif pure.type == PureType.EXEC:
            self.exec_ops[pure.get_name()] = pure
        elif pure.type == PureType.LET:
            self.read_ops[pure.get_name()] = pure
        elif pure.type == PureType.C_CODE:
            # C code used only inline
            pass
        else:
            raise NotImplementedError(f"Can not add Pure of type {pure.type}")

    def add_effect(self, effect: Effect):
        self.write_ops[effect.get_name()] = effect

    def add_hybrid(self, hybrid: Hybrid):
        self.exec_ops[hybrid.get_name()] = hybrid
        self.write_ops[hybrid.get_name()] = hybrid

    def has_op(self, name: str) -> bool:
        if name in self.read_ops:
            return True
        elif name in self.exec_ops:
            return True
        elif name in self.write_ops:
            return True
        return False

    def get_op_by_name(self, name: str):
        if name in self.read_ops:
            return self.read_ops[name]
        elif name in self.exec_ops:
            return self.exec_ops[name]
        elif name in self.write_ops:
            return self.write_ops[name]
        else:
            raise ValueError(f'Did not find op: "{name}"!')

    def rm_op_by_name(self, name: str) -> None:
        if name in self.read_ops:
            pure = self.read_ops.pop(name)
            if pure.value_type.group & VTGroup.HYBRID_LVAR:
                self.update_hybrid_ref(pure)
        if name in self.exec_ops:
            self.exec_ops.pop(name)
        if name in self.write_ops:
            self.write_ops.pop(name)

    def update_hybrid_ref(self, pure):
        # Remove the reference from the hybrid
        h_tmp_name = pure.get_name()
        h_seq: Sequence = self.hybrid_effect_dict[h_tmp_name]
        hybrid = (
            h_seq.effect_ops[0]
            if isinstance(h_seq.effect_ops[0], Hybrid)
            else h_seq.effect_ops[1]
        )
        hybrid.references_set.remove(pure)
        if len(hybrid.references_set) == 0:
            # Last reference removed, remove the hybrid
            self.hybrid_effect_dict.pop(h_tmp_name)
            self.rm_op_by_name(h_seq.get_name())
            self.rm_op_by_name(h_seq.effect_ops[0].get_name())
            self.rm_op_by_name(h_seq.effect_ops[1].get_name())

    def clear(self):
        """Removes all previously added ops."""
        self.read_ops.clear()
        self.exec_ops.clear()
        self.write_ops.clear()
        self.let_ops.clear()
        self.op_count = 0

    def is_empty(self) -> bool:
        return (
            len(self.read_ops) == 0
            and len(self.exec_ops) == 0
            and len(self.write_ops) == 0
            and len(self.let_ops) == 0
        )
