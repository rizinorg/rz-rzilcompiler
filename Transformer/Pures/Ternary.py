# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import Pure, ValueType
from Transformer.Pures.PureExec import PureExec
from Transformer.helper import exc_if_types_not_match


class Ternary(PureExec):

    def __init__(self, name: str, cond: Pure, then_p: Pure, else_p: Pure):
        PureExec.__init__(self, name, [cond, then_p, else_p], then_p.value_type)

    def il_exec(self):
        return f'ITE({self.ops[0].il_read()}, {self.ops[1].il_read()}, {self.ops[2].il_read()})'
