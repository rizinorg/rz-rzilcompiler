# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import re

from lark import Token

from Transformer.Pures.Pure import ValueType


def get_value_type_from_reg_type(token_list: list) -> ValueType:
    """Determines the size for Hexagon registers by their parse tree tokens."""
    reg_type: Token = token_list[0].value  # R, P, V, Q etc.
    reg_access = token_list[1].type  # SRC/DEST/DEST_PAIR etc.

    if reg_type in ["R", "C", "M", "N"]:
        size = 32
    elif reg_type == "P":
        size = 8
    elif reg_type == "V":
        size = 1024
    elif reg_type == "Q":
        size = 128
    else:
        raise NotImplementedError(f"Register of reg type {reg_type} not handled.")

    if "PAIR" in reg_access:
        size *= 2
    # Register content is signed by default (see QEMUs tcg functions generating scripts).
    return ValueType(True, size)


def get_c_type_by_value_type(val_type: ValueType) -> str:
    """Returns the value type for the given C integer type."""

    res = ""
    if val_type.signed:
        res += "uint"
    else:
        res += "int"
    res += str(val_type.bit_width) + "_t"
    return res


def get_num_base_by_token(token: Token):
    if token.type == "HEX_NUMBER":
        return 16
    elif token.type == "DEC_NUMBER":
        return 10
    else:
        raise NotImplementedError(f"Number base {token.type} not implemented.")


def get_value_type_by_c_number(items: [Token]) -> ValueType:
    """Returns the value type for a list of parser tree tokens of a number."""
    try:
        val = int(items[1], get_num_base_by_token(items[1]))
    except Exception as e:
        raise NotImplementedError(f"Can not determine number format.\n\n{e}")

    prefix = items[0] if items[0] else ""
    postfix = items[2] if items[2] else ""

    c_signed_types_postfix = ["LL"]
    c_unsigned_types_postfix = ["ULL", "U"]

    if postfix != "" and (
        postfix not in c_signed_types_postfix
        and postfix not in c_unsigned_types_postfix
    ):
        raise NotImplementedError(f"Unsupported number postfix {postfix}")

    size = 32
    signed = False
    if val < 0 or prefix == "-" or postfix in c_signed_types_postfix:
        signed |= True

    if postfix == "ULL" or postfix == "LL":
        size = 64
    return ValueType(signed, size)


# SPECIFIC FOR: Hexagon
def get_value_type_by_isa_imm(items: Token) -> ValueType:
    """Returns the value type for an immediate parser tree token."""

    imm_char = items[0]
    signed = False
    if re.search(r"[rRsS]", imm_char):
        signed = True

    # Immediate size is not encoded in the short code.
    return ValueType(signed, 32)
