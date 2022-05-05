# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pure import Pure, PureType


class GlobalVar(Pure):
    name = ""

    def __init__(self, name: str):
        super().init(name, PureType.GLOBAL)

    def code_read(self):
        return f'VARG({self.name})'
