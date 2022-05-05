#!/usr/bin/env python3

from lark import Lark
from Tests.testcases import behaviors


def test_parser():
    with open("../Parser/Grammars/Hexagon/ProgRefManual_Grammar.lark") as f:
        grammar = "".join(f.readlines())
    parser = Lark(grammar, start="fbody", ambiguity="explicit", parser="earley")
    correct = 0
    fail = 0
    fail_msg = []
    trees = []
    for beh in behaviors:
        try:
            tree = parser.parse(beh)
            trees.append((beh, tree.pretty()))
            correct += 1
        except Exception as e:
            fail_msg.append(e)
            fail += 1
    print("\n\nParsed {} Not parsed {}".format(correct, fail))
    if fail == 0:
        print("SUCCESSFULLY PARSED\n")
    else:
        for i, m in enumerate(fail_msg):
            print("\n" + ("#" * 20) + "\n")
            print(m)
            print("\n" + ("#" * 20) + "\n")
            a = input("Failed test #{} - Print next [q=quit] > ".format(i))
            if a == "q":
                exit()


if __name__ == "__main__":
    test_parser()

