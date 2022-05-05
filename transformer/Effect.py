# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from enum import Enum


class PureTypes(Enum):
    SETG = (0,)
    SETL = (1,)
    STOREW = (2,)
    STORE = (3,)


class Effect:
    """
    Generates statements like `SETG(<Pure>, <Pure>)`.
    """
