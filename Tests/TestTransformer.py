#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import traceback
from Transformer.ILOpsHolder import ILOpsHolder

from lark.exceptions import VisitError

from ArchEnum import ArchEnum
from Transformer.RZILTransformer import RZILTransformer
from Tests.testcases import transform_test
from lark import Lark


class TestTransformer:

    def test_transformer(self):
        with open("/home/user/repos/rzil-compiler/Resources/Hexagon/grammar.lark") as f:
            grammar = "".join(f.readlines())
        parser = Lark(grammar, start="fbody", parser="earley", debug=True)
        for beh in transform_test:
            print(f'Test behavior: f{beh}')
            try:
                tree = parser.parse(beh)
                print(tree.pretty())
                print(RZILTransformer(ArchEnum.HEXAGON).transform(tree))
                ILOpsHolder().clear()
            except VisitError as e:
                print(e)
                raise e.orig_exc


if __name__ == "__main__":
    TestTransformer().test_transformer()
