# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Token


def get_num_base_by_token(token: Token):
    if token.type == "HEX_NUMBER":
        return 16
    elif token.type == "DEC_NUMBER":
        return 10
    else:
        raise NotImplementedError(f"Number base {token.type} not implemented.")
