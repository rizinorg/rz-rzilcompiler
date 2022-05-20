# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Token


def determine_reg_size(token_list: list) -> int:
    """ Determines the size for Hexagon registers by their parse tree tokens. """
    size = -1
    reg_type: Token = token_list[0].value  # R, P, V, Q etc.
    reg_access = token_list[1].type  # SRC/DEST/DEST_PAIR etc.

    if reg_type == 'R' or reg_type == 'C':
        size = 32
    elif reg_type == 'P':
        size = 8
    elif reg_type == 'V':
        size = 1024
    elif reg_type == 'Q':
        size = 128
    else:
        NotImplementedError('')

    if 'PAIR' in reg_access:
        size *= 2
    return size
