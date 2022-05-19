# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Exceptions import OverloadException
from Transformer.Effect import Effect, EffectType
from Transformer.Pure import Pure, PureType
from enum import Enum


class Add(Pure):
    a = None
    b = None

    def __init__(self, name: str, a: Pure, b: Pure):
        self.a = a
        self.b = b

        super().__init__(name, PureType.EXEC, max(self.a.size, self.b.size))

    def get_isa_name(self):
        """ Returns the name of the RzILOpPure variable. """
        return self.name

    def il_exec(self):
        return f'ADD({self.a.il_read()}, {self.b.il_read()}'

    def il_init_var(self):
        init = f'RzIlOpPure *{self.get_name()} = {self.il_exec()});'
        return init
