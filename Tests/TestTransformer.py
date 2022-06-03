# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
from lark.exceptions import VisitError

from Transformer.RZILTransformer import RZILTransformer
from Tests.testcases import transform_test
from lark import Lark


class TestTransformer:

    def test_transformer(self):
        with open("/home/user/repos/rzil-hexagon/Resources/Hexagon/grammar.lark") as f:
            grammar = "".join(f.readlines())
        parser = Lark(grammar, start="fbody")
        for beh in transform_test:
            print(f'Test behavior: f{beh}')
            try:
                tree = parser.parse(beh)
                print(tree.pretty())
                print(RZILTransformer().transform(tree))
            except VisitError as e:
                print(e)
                raise e.orig_exc


if __name__ == "__main__":
    TestTransformer().test_transformer()