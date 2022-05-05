# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum


class PureTypes(Enum):
    ADD = (0,)
    SUB = (1,)
    MUL = (2,)
    DIV = (3,)
    MOD = (4,)
    POW = (5,)
    LT = (6,)
    LE = (7,)
    GT = (8,)
    GE = (9,)
    AND = (10,)
    OR = (11,)
    XOR = (12,)
    LOADW = (100,)


class Pure:
    """
    Pures generate statements of the for `RzILOpPure var = <Pure>`.
    """

    def init(self):
        pass
