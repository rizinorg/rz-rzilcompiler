#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import re
import unittest

from Configuration import Conf, InputFile
from Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
from ExpectedOutput import ExpectedOutput
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


class TestTransforming(unittest.TestCase):
    debug = False
    insn_behavior: dict[str:tuple] = dict()

    @classmethod
    def setUpClass(cls):
        cls.insn_behavior = get_hexagon_insn_behavior()
        cls.parser = get_hexagon_parser()

    def compile_behavior(self, behavior: str) -> Exception:
        exception = None
        try:
            tree = self.parser.parse(behavior)
            RZILTransformer(ArchEnum.HEXAGON).transform(tree)
        except UnexpectedToken as e:
            # Parser got unexpected token
            exception = e
        except UnexpectedCharacters as e:
            # Lexer can not match character to token.
            exception = e
        except UnexpectedEOF as e:
            # Parser expected a token but got EOF
            exception = e
        except VisitError as e:
            # Something went wrong in our transformer.
            exception = e
        except Exception as e:
            exception = e
        finally:
            ILOpsHolder().clear()

        if self.debug and exception:
            raise exception

        return exception

    def test_J2_jump(self):
        behavior = self.insn_behavior["J2_jump"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpr(self):
        behavior = self.insn_behavior["J2_jumpr"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpt(self):
        behavior = self.insn_behavior["J2_jumpt"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpf(self):
        behavior = self.insn_behavior["J2_jumpf"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumprt(self):
        behavior = self.insn_behavior["J2_jumprt"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumprf(self):
        behavior = self.insn_behavior["J2_jumprf"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J4_cmpgti_tp0_jump_t(self):
        behavior = self.insn_behavior["J4_cmpgti_tp0_jump_t"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

        behavior = self.insn_behavior["J4_cmpgti_tp0_jump_t"][1]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_call(self):
        behavior = self.insn_behavior["J2_call"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_loop0r(self):
        behavior = self.insn_behavior["J2_loop0r"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_L2_loadrd_io(self):
        behavior = self.insn_behavior["L2_loadrd_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_storeri_io(self):
        behavior = self.insn_behavior["S2_storeri_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_storerd_io(self):
        behavior = self.insn_behavior["S2_storerd_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_L4_return(self):
        behavior = self.insn_behavior["L4_return"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S4_storeiri_io(self):
        behavior = self.insn_behavior["S4_storeiri_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_cmpgtu(self):
        behavior = self.insn_behavior["C2_cmpgtu"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_cmpgti(self):
        behavior = self.insn_behavior["C2_cmpgti"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_xor(self):
        behavior = self.insn_behavior["C2_xor"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_muxii(self):
        behavior = self.insn_behavior["C2_muxii"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_M2_mpyi(self):
        behavior = self.insn_behavior["M2_mpyi"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_sub(self):
        behavior = self.insn_behavior["A2_sub"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_paddfnew(self):
        behavior = self.insn_behavior["A2_paddfnew"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_psubfnew(self):
        behavior = self.insn_behavior["A2_psubfnew"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_paddit(self):
        behavior = self.insn_behavior["A2_paddit"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_addi(self):
        behavior = self.insn_behavior["A2_addi"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_abs(self):
        behavior = self.insn_behavior["A2_abs"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_nop(self):
        behavior = self.insn_behavior["A2_nop"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A4_ext(self):
        behavior = self.insn_behavior["A4_ext"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_tfr(self):
        behavior = self.insn_behavior["A2_tfr"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_tfrsi(self):
        behavior = self.insn_behavior["A2_tfrsi"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_combinew(self):
        behavior = self.insn_behavior["A2_combinew"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_combineii(self):
        behavior = self.insn_behavior["A2_combineii"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_subri(self):
        behavior = self.insn_behavior["A2_subri"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_lsr_i_vw(self):
        behavior = self.insn_behavior["S2_lsr_i_vw"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_lsl_r_vw(self):
        behavior = self.insn_behavior["S2_lsl_r_vw"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_cl0(self):
        behavior = self.insn_behavior["S2_cl0"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_addi(self):
        behavior = self.insn_behavior["SA1_addi"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_tfr(self):
        behavior = self.insn_behavior["SA1_tfr"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_seti(self):
        behavior = self.insn_behavior["SA1_seti"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_combinezr(self):
        behavior = self.insn_behavior["SA1_combinezr"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_combine1i(self):
        behavior = self.insn_behavior["SA1_combine1i"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL1_loadri_io(self):
        behavior = self.insn_behavior["SL1_loadri_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_loadrh_io(self):
        behavior = self.insn_behavior["SL2_loadrh_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_loadrd_sp(self):
        behavior = self.insn_behavior["SL2_loadrd_sp"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_jumpr31_t(self):
        behavior = self.insn_behavior["SL2_jumpr31_t"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_storeh_io(self):
        behavior = self.insn_behavior["SS2_storeh_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_stored_sp(self):
        behavior = self.insn_behavior["SS2_stored_sp"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_storew_sp(self):
        behavior = self.insn_behavior["SS2_storew_sp"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_allocframe(self):
        behavior = self.insn_behavior["SS2_allocframe"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)


class TestTransformerMeta(unittest.TestCase):
    debug = False
    insn_behavior: dict[str:tuple] = dict()

    @classmethod
    def setUpClass(cls):
        cls.insn_behavior = get_hexagon_insn_behavior()
        cls.parser = get_hexagon_parser()

    def compile_behavior(self, behavior: str) -> list[str]:
        try:
            tree = self.parser.parse(behavior)
            transformer = RZILTransformer(ArchEnum.HEXAGON)
            transformer.transform(tree)
            return transformer.ext.get_meta()
        except UnexpectedToken as e:
            # Parser got unexpected token
            exception = e
        except UnexpectedCharacters as e:
            # Lexer can not match character to token.
            exception = e
        except UnexpectedEOF as e:
            # Parser expected a token but got EOF
            exception = e
        except VisitError as e:
            # Something went wrong in our transformer.
            exception = e
        except Exception as e:
            exception = e
        finally:
            ILOpsHolder().clear()
        raise exception

    def test_J2_jump(self):
        behavior = self.insn_behavior["J2_jump"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(meta, ["HEX_IL_INSN_ATTR_BRANCH"])

    def test_J2_jumpt(self):
        behavior = self.insn_behavior["J2_jumpt"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(meta, ["HEX_IL_INSN_ATTR_COND", "HEX_IL_INSN_ATTR_BRANCH"])

    def test_J4_cmpgti_tp0_jump_t(self):
        behavior = self.insn_behavior["J4_cmpgti_tp0_jump_t"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(
            meta, ["HEX_IL_INSN_ATTR_WPRED", "HEX_IL_INSN_ATTR_WRITE_P0"]
        )

        behavior = self.insn_behavior["J4_cmpgti_tp0_jump_t"][1]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(
            meta,
            [
                "HEX_IL_INSN_ATTR_COND",
                "HEX_IL_INSN_ATTR_NEW",
                "HEX_IL_INSN_ATTR_BRANCH",
            ],
        )

    def test_J2_call(self):
        behavior = self.insn_behavior["J2_call"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(meta, ["HEX_IL_INSN_ATTR_BRANCH"])

    def test_J2_loop0r(self):
        behavior = self.insn_behavior["J2_loop0r"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(meta, ["HEX_IL_INSN_ATTR_NONE"])

    def test_L2_loadrd_io(self):
        behavior = self.insn_behavior["L2_loadrd_io"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(meta, ["HEX_IL_INSN_ATTR_MEM_READ"])

    def test_S2_storerd_io(self):
        behavior = self.insn_behavior["S2_storerd_io"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertEqual(meta[0], "HEX_IL_INSN_ATTR_MEM_WRITE")

    def test_L4_return(self):
        behavior = self.insn_behavior["L4_return"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(
            meta, ["HEX_IL_INSN_ATTR_MEM_READ", "HEX_IL_INSN_ATTR_BRANCH"]
        )

    def test_L4_return_t(self):
        behavior = self.insn_behavior["L4_return_t"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(
            meta,
            [
                "HEX_IL_INSN_ATTR_COND",
                "HEX_IL_INSN_ATTR_MEM_READ",
                "HEX_IL_INSN_ATTR_BRANCH",
            ],
        )

    def test_C4_and_and(self):
        behavior = self.insn_behavior["C4_and_and"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(meta, ["HEX_IL_INSN_ATTR_WPRED"])

    def test_A2_nop(self):
        behavior = self.insn_behavior["A2_nop"][0]
        meta: list[str] = self.compile_behavior(behavior)
        self.assertListEqual(meta, ["HEX_IL_INSN_ATTR_NONE"])


class TestTransformerOutput(unittest.TestCase):
    debug = False
    insn_behavior: dict[str:tuple] = dict()

    @classmethod
    def setUpClass(cls):
        cls.insn_behavior = get_hexagon_insn_behavior()
        cls.parser = get_hexagon_parser()

    def compile_behavior(self, behavior: str) -> list[str]:
        try:
            tree = self.parser.parse(behavior)
            transformer = RZILTransformer(ArchEnum.HEXAGON)
            return transformer.transform(tree)
        except UnexpectedToken as e:
            # Parser got unexpected token
            exception = e
        except UnexpectedCharacters as e:
            # Lexer can not match character to token.
            exception = e
        except UnexpectedEOF as e:
            # Parser expected a token but got EOF
            exception = e
        except VisitError as e:
            # Something went wrong in our transformer.
            exception = e
        except Exception as e:
            exception = e
        finally:
            ILOpsHolder().clear()
        raise exception

    def test_Y2_barrier(self):
        behavior = self.insn_behavior["Y2_barrier"][0]
        output = self.compile_behavior(behavior)

        self.assertEqual(output, ExpectedOutput["Y2_barrier"])


if __name__ == "__main__":
    tester = TestTransforming()
    tester.test_J2_jump()
    tester.test_J2_jumpr()
    tester.test_J2_jumpt()
    tester.test_J2_jumpf()
    tester.test_J2_jumprt()
    tester.test_J2_jumprf()
    tester.test_J4_cmpgti_tp0_jump_t()
    tester.test_J2_call()
    tester.test_J2_loop0r()
    tester.test_L2_loadrd_io()
    tester.test_S2_storeri_io()
    tester.test_S2_storerd_io()
    tester.test_L4_return()
    tester.test_S4_storeiri_io()
    tester.test_C2_cmpgtu()
    tester.test_C2_cmpgti()
    tester.test_C2_xor()
    tester.test_C2_muxii()
    tester.test_M2_mpyi()
    tester.test_A2_sub()
    tester.test_A2_paddfnew()
    tester.test_A2_psubfnew()
    tester.test_A2_paddit()
    tester.test_A2_addi()
    tester.test_A2_abs()
    tester.test_A2_nop()
    tester.test_A4_ext()
    tester.test_A2_tfr()
    tester.test_A2_tfrsi()
    tester.test_A2_combinew()
    tester.test_A2_combineii()
    tester.test_A2_subri()
    tester.test_S2_lsr_i_vw()
    tester.test_S2_lsl_r_vw()
    tester.test_S2_cl0()
    tester.test_SA1_addi()
    tester.test_SA1_tfr()
    tester.test_SA1_seti()
    tester.test_SA1_combinezr()
    tester.test_SA1_combine1i()
    tester.test_SL1_loadri_io()
    tester.test_SL2_loadrh_io()
    tester.test_SL2_loadrd_sp()
    tester.test_SL2_jumpr31_t()
    tester.test_SS2_storeh_io()
    tester.test_SS2_stored_sp()
    tester.test_SS2_storew_sp()
    tester.test_SS2_allocframe()

    tester = TestTransformerMeta()
    tester.test_J2_jump()
    tester.test_J2_jumpt()
    tester.test_J4_cmpgti_tp0_jump_t()
    tester.test_J2_call()
    tester.test_J2_loop0r()
    tester.test_L2_loadrd_io()
    tester.test_S2_storerd_io()
    tester.test_L4_return()
    tester.test_A2_nop()

    tester = TestTransformerOutput()
    tester.test_Y2_barrier()
