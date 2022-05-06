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

        super().init(name, PureType.EXEC)

    def get_isa_name(self):
        """ Returns the name of the RzILOpPure variable. """
        return self.name

    def code_exec(self):
        return f'ADD({self.a.code_read()}, {self.b.code_read()}'

    def code_init_var(self):
        init = f'RzIlOpPure *{self.get_name()} = {self.code_exec()});'
        return init
