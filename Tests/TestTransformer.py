#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import traceback
import unittest

from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.RZILTransformer import RZILTransformer
from ArchEnum import ArchEnum

from lark import Lark
from lark.exceptions import VisitError



class TestTransformer:

    def test_transformer(self):
        with open("/home/user/repos/rzil-compiler/Resources/Hexagon/grammar.lark") as f:
            grammar = "".join(f.readlines())
        parser = Lark(grammar, start="fbody", parser="earley", debug=True)
        for beh in transform_test:
            print(f'Test behavior: f{beh}')
            tree = '########'
            try:
                tree = parser.parse(beh)
                print(tree.pretty())
                print(RZILTransformer(ArchEnum.HEXAGON).transform(tree))
                ILOpsHolder().clear()
            except VisitError as e:
                print(e)
                print(e.orig_exc)
                print(beh)
                input('Raise original exc')
                raise e.orig_exc
                exit()


if __name__ == "__main__":
    TestTransformer().test_transformer()
