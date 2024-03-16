#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import re
import unittest

from lark import Lark

from rzilcompiler.ArchEnum import ArchEnum
from rzilcompiler.Parser import Parser, ParserException
from rzilcompiler.Configuration import Conf, InputFile
from rzilcompiler.Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon


def get_hexagon_insn_behavior() -> dict[str:tuple]:
    collection = dict()
    # Get instruction behaviors from resolved shortcode
    with open(Conf.get_path(InputFile.HEXAGON_PP_SHORTCODE_RESOLVED_H)) as f:
        for line in f.readlines():
            if line[:5] != "insn(":
                continue
            matches = re.search(r"insn\((\w+), (.*)\)$", line)
            insn_name = matches.group(1)
            insn_behavior = matches.group(2)
            if "__COMPOUND_PART1__" in insn_behavior:
                behaviors = PreprocessorHexagon.split_compounds(insn_behavior)
            else:
                behaviors = [insn_behavior]

            collection[insn_name] = behaviors
    return collection


def get_hexagon_parser() -> Lark:
    # Setup parser
    with open(Conf.get_path(InputFile.GRAMMAR, ArchEnum.HEXAGON)) as f:
        grammar = "".join(f.readlines())
    return Lark(grammar, start="fbody", parser="earley")


class TestParser(unittest.TestCase):
    debug = False
    insn_behavior: dict[str:tuple] = dict()

    @classmethod
    def setUpClass(cls):
        cls.insn_behavior = get_hexagon_insn_behavior()

    def test_threading_exception(self):
        shortcodes = dict()
        shortcodes["faulty_input"] = ["{"]

        exc = Parser.parse(shortcodes)
        self.assertTrue(isinstance(exc["faulty_input"].exception, ParserException))


if __name__ == "__main__":
    TestParser().main()
