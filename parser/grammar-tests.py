#!/usr/bin/env python3

from lark import Lark
from testcases import behaviors

if __name__ == '__main__':
    with open('Hexagon/manual-grammar.lark') as f:
        grammar = ''.join(f.readlines())
    parser = Lark(grammar, start='fbody', ambiguity='explicit')#, ambiguity="explicit")
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
    print('\n\nParsed {} Not parsed {}'.format(correct, fail))
    if (fail == 0):
        print("SUCCESSFUL PARSED\n")
    else:
        for i, m in enumerate(fail_msg):
            print('\n' + ('#' * 20) + '\n')
            print(m)
            print('\n' + ('#' * 20) + '\n')
            a = input('Failed test #{} - Print next [q=quit] > '.format(i))
            if a == 'q':
                exit()

#    for i, m in enumerate(trees):
#        print("Syntax: {}".format(m[0]))
#        print('\n' + ('#' * 20) + '\n')
#        print(m[1])
#        print('\n' + ('#' * 20) + '\n')
#        #a = input('Test #{} - Print next [q=quit] > '.format(i))
#        #if a == 'q':
#        #    exit()
