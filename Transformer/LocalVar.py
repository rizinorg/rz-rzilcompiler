# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Pure import Pure, PureType


class LocalVar(Pure):
    name = ""

    def __init__(self, name: str):
        super().__init__(name, PureType.LOCAL)

    def il_read(self):
        return f'VARL({self.name})'
