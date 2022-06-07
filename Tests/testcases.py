# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

transform_test = [
    """
    {; riV = (riV & ~(4 - 1)); JUMP((HEX_REG_ALIAS_PC)+riV);}
    """,
]
