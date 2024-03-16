# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only


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
    """Returns the content of a list and clears it."""
    result, l[:] = l[:], []
    return result
