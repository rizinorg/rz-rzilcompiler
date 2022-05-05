from Transformer.ManualTransformer import ManualTransformer
from testcases import transform_test
from lark import Lark


def test_transformer():
    with open("parser/Grammars/Hexagon/manual-grammar.lark") as f:
        grammar = "".join(f.readlines())
    parser = Lark(grammar, start="fbody")
    for beh in transform_test:
        try:
            tree = parser.parse(beh)
            ManualTransformer.transform(tree)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    test_transformer()