# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer


class ManualTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """

    # Returned value replaces node in tree
    # Transformers/Visitors are called bottom up! First leaves then parents
    def reg(self, items):
        print(f'reg: {items}')
        return f"{items[0]}{items[1]}"

    def imm(self, items):
        print(f'reg: {items}')
        return f"{items[0]}{items[1]}"

    def assign(self, items):
        print(f'assign {items}')
        return "ASSIGN"

    def add(self, items):
        print(f'add: {items}')
        return "ADD"