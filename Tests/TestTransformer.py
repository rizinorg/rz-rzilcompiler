#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import traceback
import unittest

from Configuration import Conf, InputFile
from Tests.testcases import insn_tests_hexagon
from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.RZILTransformer import RZILTransformer
from ArchEnum import ArchEnum

from lark import Lark
from lark.exceptions import (
    VisitError,
    UnexpectedToken,
    UnexpectedCharacters,
    UnexpectedEOF,
)


class TestTransformer(unittest.TestCase):
    debug = True

    def test_transform_insns_hexagon(self):
        """
        Tests exception free parsing and transformation of Hexagon instructions.
        """
        with open(Conf.get_path(InputFile.GRAMMAR, ArchEnum.HEXAGON)) as f:
            grammar = "".join(f.readlines())
        parser = Lark(grammar, start="fbody", parser="earley")
        for insn, behavior in insn_tests_hexagon.items():
            exc_unexpected_token_raised = False
            exc_unexpected_char_raised = False
            exc_unexpected_eof_raised = False
            exc_visit_error_raised = False
            exc_general_raised = False
            exception = None
            try:
                tree = parser.parse(behavior)
                RZILTransformer(ArchEnum.HEXAGON).transform(tree)
                ILOpsHolder().clear()
            except UnexpectedToken as e:
                # Parser got unexpected token
                exc_unexpected_token_raised = True
                exception = e
            except UnexpectedCharacters as e:
                # Lexer can not match character to token.
                exc_unexpected_char_raised = True
                exception = e
            except UnexpectedEOF as e:
                # Parser expected a token but got EOF
                exc_unexpected_eof_raised = True
                exception = e
            except VisitError as e:
                # Something went wrong in the transformer
                exc_visit_error_raised = True
                exception = e
            except Exception as e:
                exc_general_raised = True
                exception = e

            if self.debug and exception:
                raise exception

            self.assertFalse(
                exc_unexpected_token_raised,
                f"{insn} - unexpected_token_raised {traceback.print_exception(exception)}",
            )
            self.assertFalse(
                exc_unexpected_char_raised,
                f"{insn} - unexpected_char_raised {traceback.print_exception(exception)}",
            )
            self.assertFalse(
                exc_unexpected_eof_raised,
                f"{insn} - unexpected_eof_raised {traceback.print_exception(exception)}",
            )
            self.assertFalse(
                exc_visit_error_raised,
                f"{insn} - visit_error_raised {traceback.print_exception(exception)}",
            )
            self.assertFalse(
                exc_general_raised,
                f"{insn} - general_exception_raised {traceback.print_exception(exception)}",
            )


if __name__ == "__main__":
    test_case = TestTransformer()
    test_case.test_transform_insns_hexagon()
