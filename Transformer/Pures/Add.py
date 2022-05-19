# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pure import Pure
from Transformer.Pures.PureExec import PureExec


class Add(PureExec):
    a = None
    b = None

    def __init__(self, name: str, a: Pure, b: Pure):
        self.a = a
        self.b = b

        super().__init__(name, max(self.a.size, self.b.size))

    def il_exec(self):
        return f'ADD({self.a.il_read()}, {self.b.il_read()}'
