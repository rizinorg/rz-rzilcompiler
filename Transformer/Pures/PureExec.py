# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pure import Pure, PureType


class PureExec(Pure):

    def __init__(self, name: str, size: int):
        super().__init__(name, PureType.EXEC, size)

    def il_init_var(self):
        init = f'RzIlOpPure *{self.get_name()} = {self.il_exec()});'
        return init
