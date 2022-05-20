# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Token

from Transformer.Pures.Pure import ValueType


def get_value_type_from_reg_type(token_list: list) -> ValueType:
    """ Determines the size for Hexagon registers by their parse tree tokens. """
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
        raise NotImplementedError('')

    if 'PAIR' in reg_access:
        size *= 2
    return ValueType('register', False, size)


def get_value_type_by_c_type(c_type: str) -> ValueType:
    """ Returns the size in bits for the given C integer type. """

    if c_type == 'short':
        return ValueType(c_type, True, 16)
    else:
        raise NotImplementedError('')
