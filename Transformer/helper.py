# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import ValueType


def exc_if_types_not_match(a: ValueType, b: ValueType):
    if a != b:
        raise ValueError("Value types don't match.")