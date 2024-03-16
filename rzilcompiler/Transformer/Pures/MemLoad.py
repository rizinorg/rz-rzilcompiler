# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzilcompiler.Transformer.Pures.Pure import Pure
from rzilcompiler.Transformer.ValueType import ValueType
from rzilcompiler.Transformer.Pures.PureExec import PureExec


class MemAccessType:
    """Stores information about the memory access."""

    def __init__(self, val_type: ValueType, reads_mem: bool):
        self.val_type = val_type  # Type of the value read or written
        self.reads_mem = reads_mem  # Flag: Memory is read
        self.writes_mem = not reads_mem  # Flag: Memory is written


class MemLoad(PureExec):
    def __init__(self, name: str, va: Pure, acc_type: MemAccessType):
        self.acc_type = acc_type
        self.va = va
        PureExec.__init__(self, name, [va], acc_type.val_type)

    def il_exec(self):
        return f"LOADW({self.acc_type.val_type.bit_width}, {self.va.il_read()})"

    def __str__(self):
        return f"mem_load_{self.acc_type.val_type.bit_width}({self.va})"
