#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import re
import unittest

from Configuration import Conf, InputFile
from Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
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
    debug = False
    insns_bahvior: dict[str:tuple] = dict()

    @classmethod
    def setUpClass(cls):
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

                cls.insns_bahvior[insn_name] = behaviors

        # Setup parser
        with open(Conf.get_path(InputFile.GRAMMAR, ArchEnum.HEXAGON)) as f:
            grammar = "".join(f.readlines())
        cls.parser = Lark(grammar, start="fbody", parser="earley")

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
        behavior = self.insns_bahvior["J2_jump"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpr(self):
        behavior = self.insns_bahvior["J2_jumpr"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpt(self):
        behavior = self.insns_bahvior["J2_jumpt"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpf(self):
        behavior = self.insns_bahvior["J2_jumpf"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumprt(self):
        behavior = self.insns_bahvior["J2_jumprt"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumprf(self):
        behavior = self.insns_bahvior["J2_jumprf"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J4_cmpgti_tp0_jump_t(self):
        behavior = self.insns_bahvior["J4_cmpgti_tp0_jump_t"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

        behavior = self.insns_bahvior["J4_cmpgti_tp0_jump_t"][1]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_call(self):
        behavior = self.insns_bahvior["J2_call"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_loop0r(self):
        behavior = self.insns_bahvior["J2_loop0r"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_L2_loadrd_io(self):
        behavior = self.insns_bahvior["L2_loadrd_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_storeri_io(self):
        behavior = self.insns_bahvior["S2_storeri_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_storerd_io(self):
        behavior = self.insns_bahvior["S2_storerd_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_L4_return(self):
        behavior = self.insns_bahvior["L4_return"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S4_storeiri_io(self):
        behavior = self.insns_bahvior["S4_storeiri_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_cmpgtu(self):
        behavior = self.insns_bahvior["C2_cmpgtu"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_cmpgti(self):
        behavior = self.insns_bahvior["C2_cmpgti"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_xor(self):
        behavior = self.insns_bahvior["C2_xor"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_muxii(self):
        behavior = self.insns_bahvior["C2_muxii"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_M2_mpyi(self):
        behavior = self.insns_bahvior["M2_mpyi"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_sub(self):
        behavior = self.insns_bahvior["A2_sub"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_paddfnew(self):
        behavior = self.insns_bahvior["A2_paddfnew"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_psubfnew(self):
        behavior = self.insns_bahvior["A2_psubfnew"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_paddit(self):
        behavior = self.insns_bahvior["A2_paddit"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_addi(self):
        behavior = self.insns_bahvior["A2_addi"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_abs(self):
        behavior = self.insns_bahvior["A2_abs"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_nop(self):
        behavior = self.insns_bahvior["A2_nop"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A4_ext(self):
        behavior = self.insns_bahvior["A4_ext"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_tfr(self):
        behavior = self.insns_bahvior["A2_tfr"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_tfrsi(self):
        behavior = self.insns_bahvior["A2_tfrsi"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_combinew(self):
        behavior = self.insns_bahvior["A2_combinew"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_combineii(self):
        behavior = self.insns_bahvior["A2_combineii"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_subri(self):
        behavior = self.insns_bahvior["A2_subri"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_lsr_i_vw(self):
        behavior = self.insns_bahvior["S2_lsr_i_vw"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_lsl_r_vw(self):
        behavior = self.insns_bahvior["S2_lsl_r_vw"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_cl0(self):
        behavior = self.insns_bahvior["S2_cl0"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_addi(self):
        behavior = self.insns_bahvior["SA1_addi"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_tfr(self):
        behavior = self.insns_bahvior["SA1_tfr"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_seti(self):
        behavior = self.insns_bahvior["SA1_seti"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_combinezr(self):
        behavior = self.insns_bahvior["SA1_combinezr"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_combine1i(self):
        behavior = self.insns_bahvior["SA1_combine1i"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL1_loadri_io(self):
        behavior = self.insns_bahvior["SL1_loadri_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_loadrh_io(self):
        behavior = self.insns_bahvior["SL2_loadrh_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_loadrd_sp(self):
        behavior = self.insns_bahvior["SL2_loadrd_sp"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_jumpr31_t(self):
        behavior = self.insns_bahvior["SL2_jumpr31_t"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_storeh_io(self):
        behavior = self.insns_bahvior["SS2_storeh_io"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_stored_sp(self):
        behavior = self.insns_bahvior["SS2_stored_sp"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_storew_sp(self):
        behavior = self.insns_bahvior["SS2_storew_sp"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_allocframe(self):
        behavior = self.insns_bahvior["SS2_allocframe"][0]
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)


if __name__ == "__main__":
    tester = TestTransformer()
    tester.test_J2_jump()
    tester.test_J2_jumpr()
    tester.test_J2_jumpt()
    tester.test_J2_jumpf()
    tester.test_J2_jumprt()
    tester.test_J2_jumprf()
    tester.test_J4_cmpgti_tp0_jump_t_part0()
    tester.test_J4_cmpgti_tp0_jump_t_part1()
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
