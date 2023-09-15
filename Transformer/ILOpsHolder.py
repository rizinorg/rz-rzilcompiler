# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect
from Transformer.Hybrids.Hybrid import Hybrid
from Transformer.Pures.Pure import Pure, PureType
from Transformer.Pures.Variable import Variable


class ILOpsHolder:
    read_ops: dict = dict()
    exec_ops: dict = dict()
    write_ops: dict = dict()
    let_ops: dict = dict()  # immutable LET vars.
    op_count = 0

    def get_op_count(self):
        cnt = self.op_count
        self.op_count += 1
        return cnt

    def add_op(self, op):
        """
        Adds an IL operation and appends an id to its
        name to make the name unique.
        """
        if not isinstance(op, Variable):
            # Variables already have a unique name
            op.set_name(f"{op.get_name()}_{self.get_op_count()}")
        if isinstance(op, Pure):
            self.add_pure(op)
        elif isinstance(op, Effect):
            self.add_effect(op)
        elif isinstance(op, Hybrid):
            self.add_hybrid(op)
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
        self.exec_ops[hybrid.get_name()] = hybrid.ops
        self.write_ops[hybrid.get_name()] = hybrid.effect_ops

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
            return self.read_ops.pop(name)
        elif name in self.exec_ops:
            return self.exec_ops.pop(name)
        elif name in self.write_ops:
            return self.write_ops.pop(name)
        else:
            raise ValueError(f'Did not find op: "{name}"!')

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
