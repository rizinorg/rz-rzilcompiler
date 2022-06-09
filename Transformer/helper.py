# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.Pures.Pure import ValueType


def check_and_convert_types(a: ValueType, b: ValueType) -> (ValueType, ValueType):
    """ Compares both value types against each other and converts them according to
        Chapter 6.3.1.8 of ISO/IEC 9899:201x (C11 Standard).
        Please note that we do not follow the rank definition from the standard.
        Here: Rank = width of type. Which should be close enough.
    """

    sign_match = a.signed == b.signed
    rank_match = a.bit_width = b.bit_width
    if sign_match and rank_match:
        return a, b

    if sign_match:
        if a.bit_width < b.bit_width:
            a.bit_width = b.bit_width
        else:
            b.bit_width = a.bit_width
        return a, b

    a_is_signed = a.signed
    unsigned = b if a_is_signed else a
    signed = a if a_is_signed else b

    if unsigned.bit_width >= signed.bit_width:
        signed.bit_width = unsigned.bit_width
        signed.signed = False
        return (signed, unsigned) if a_is_signed else (b, a)
    else:
        unsigned.bit_width = signed.bit_width
        unsigned.signed = True
        return (signed, unsigned) if a_is_signed else (b, a)
