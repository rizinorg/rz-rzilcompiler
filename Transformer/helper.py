# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from copy import deepcopy

from Transformer.ILOpsHolder import OpCounter
from Transformer.Pures.Cast import Cast
from Transformer.Pures.Pure import ValueType, Pure


def get_smalles_val_type_for_number(num: int) -> int:
    if num & 0xffffffffffffff00 == 0:
        size = 8
    elif num & 0xffffffffffff0000 == 0:
        size = 16
    elif num & 0xffffffff00000000 == 0:
        size = 32
    else:
        size = 64
    return size


def exc_if_types_not_match(a: ValueType, b: ValueType):
    if a != b:
        raise ValueError("Value types don't match.\n"
                         f"a size: {a.bit_width} signed: {a.signed}\n"
                         f"b size: {b.bit_width} signed: {b.signed}")


def cast_operands(immutable_a: bool, **ops) -> (Pure, Pure):
    """ Casts two operands to a common type according to C11 standard.
        If immutable_op_a = True operand b is cast to the operand a type
        (Useful for assignments to global vars like registers).
        Operand are names in the order: a, b, c, ...
    """
    if 'a' not in ops and 'b' not in ops:
        raise NotImplementedError('At least operand "a" and "b" must e given.')
    a = ops['a']
    b = ops['b']
    if not a.value_type and not b.value_type:
        raise NotImplementedError('Cannot cast ops without value types.')
    if not a.value_type:
        a.value_type = b.value_type
        return a, b
    if not b.value_type:
        b.value_type = a.value_type
        return a, b

    if a.value_type == b.value_type:
        return a, b

    cname = f'cast_{OpCounter().get_op_count()}'
    if immutable_a:
        return a, Cast(cname, a.value_type, b)

    casted_a, casted_b = c11_cast(a.value_type, b.value_type)

    if casted_a.bit_width != a.value_type.bit_width or casted_a.signed != a.value_type.signed:
        a = Cast(cname, casted_a, a)
    if casted_b.bit_width != b.value_type.bit_width or casted_b.signed != b.value_type.signed:
        b = Cast(cname, casted_b, b)

    return a, b


def c11_cast(a: ValueType, b: ValueType) -> (ValueType, ValueType):
    """ Compares both value types against each other and converts them according to
        Chapter 6.3.1.8 of ISO/IEC 9899:201x (C11 Standard).
        Please note that we do not follow the rank definition from the standard.
        Here: Rank = width of type. Which should be close enough.
    """

    sign_match = a.signed == b.signed
    rank_match = a.bit_width == b.bit_width
    if sign_match and rank_match:
        return a, b
    va = deepcopy(a)
    vb = deepcopy(b)

    if sign_match:
        if va.bit_width < vb.bit_width:
            va.bit_width = vb.bit_width
        else:
            vb.bit_width = va.bit_width
        return va, vb

    a_is_signed = va.signed
    unsigned = vb if a_is_signed else va
    signed = va if a_is_signed else vb

    if unsigned.bit_width >= signed.bit_width:
        signed.bit_width = unsigned.bit_width
        signed.signed = False
    else:
        unsigned.bit_width = signed.bit_width
        unsigned.signed = True
    return (signed, unsigned) if a_is_signed else (unsigned, signed)


def flatten_list(ls: list) -> list:
    if not hasattr(ls, "__iter__") or isinstance(ls, str):
        return [ls]
    result = []
    for el in ls:
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten_list(el))
        else:
            result.append(el)
    return result


def drain_list(l: list) -> list:
    """ Returns the content of a list and clears it. """
    result, l[:] = l[:], []
    return result
