# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import Pure, PureType, ValueType


class MemAccessType:
    """ Stores information about the memory access. """
    def __init__(self, val_type: ValueType, reads_mem: bool):
        self.val_type = val_type  # Type of the value read or written
        self.reads = reads_mem  # Flag: Memory is read
        self.writes = not reads_mem  # Flag: Memory is written


class MemLoad(Pure):

    def __init__(self, name: str, va: Pure, acc_type: MemAccessType):
        self.acc_type = acc_type
        self.va = va
        super().__init__(name, PureType.GLOBAL, acc_type.val_type)

    def il_exec(self):
        return f'LOADW({self.acc_type.val_type.bit_width}, {self.va.il_read()})'
