# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Transformer.ManualTransformer import ManualTransformer
from Tests.testcases import transform_test
from lark import Lark


class TestTransformer:

    def test_transformer(self):
        with open("../Parser/Grammars/Hexagon/ProgRefManual_Grammar.lark") as f:
            grammar = "".join(f.readlines())
        parser = Lark(grammar, start="fbody")
        for beh in transform_test:
            try:
                tree = parser.parse(beh)
                print(tree.pretty())
                ManualTransformer().transform(tree)
            except Exception as e:
                print(e)


if __name__ == "__main__":
    Tests().test_transformer()