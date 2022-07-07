# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Effects.Effect import Effect
from Transformer.Hybrids.Hybrid import Hybrid
from Transformer.Pures.Pure import Pure, PureType


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


@singleton
class ILOpsHolder(object):
    read_ops = dict()
    exec_ops = dict()
    write_ops = dict()
    let_ops = dict()  # immutable LET vars.

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
            raise NotImplementedError(f'Can not add Pure of type {pure.type}')

    def add_effect(self, effect: Effect):
        self.write_ops[effect.get_name()] = effect

    def get_op_by_name(self, name: str):
        if name in self.read_ops:
            return self.read_ops[name]
        elif name in self.exec_ops:
            return self.exec_ops[name]
        elif name in self.write_ops:
            return self.write_ops[name]
        else:
            raise ValueError(f'Did not find op: "{name}"!')

    def clear(self):
        """ Removes all previously added ops. """
        self.read_ops.clear()
        self.exec_ops.clear()
        self.write_ops.clear()
        self.let_ops.clear()
