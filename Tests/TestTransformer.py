#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import unittest

from Configuration import Conf, InputFile
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

    def setUp(self):
        with open(Conf.get_path(InputFile.GRAMMAR, ArchEnum.HEXAGON)) as f:
            grammar = "".join(f.readlines())
        self.parser = Lark(grammar, start="fbody", parser="earley")

    def test_J2_jump(self):
        behavior = "{(riV); riV = (riV & ~(4 - 1)); JUMP((HEX_REG_ALIAS_PC)+riV);}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpr(self):
        behavior = "{JUMP(RsV);}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpt(self):
        behavior = "{; if (((PuV) & 1)) { (riV);riV = (riV & ~(4 - 1)); JUMP((HEX_REG_ALIAS_PC)+riV);; }}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumpf(self):
        behavior = "{; if ((!((PuV) & 1))) { (riV);riV = (riV & ~(4 - 1)); JUMP((HEX_REG_ALIAS_PC)+riV);; }}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumprt(self):
        behavior = "{; if (((PuV) & 1)) { JUMP(RsV);; }}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_jumprf(self):
        behavior = "{; if ((!((PuV) & 1))) { JUMP(RsV);; }}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J4_cmpgti_tp0_jump_t_part0(self):
        behavior = "{ if ((P0_NEW & 1)) {(riV); riV = (riV & ~(4 - 1)); JUMP((HEX_REG_ALIAS_PC)+riV);}}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J4_cmpgti_tp0_jump_t_part1(self):
        behavior = "{ P0 = (((RsV>UiV)) ? 0xff : 0x00);; }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_call(self):
        behavior = "{(riV); riV = (riV & ~(4 - 1)); (HEX_REG_ALIAS_LR = (get_npc(pkt) & (0xfffffffe))); JUMP((HEX_REG_ALIAS_PC)+riV);; }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_J2_loop0r(self):
        behavior = "{ (riV); riV = (riV & ~(4 - 1)); HEX_REG_ALIAS_SA0 = (HEX_REG_ALIAS_PC)+riV; (HEX_REG_ALIAS_LC0 = RsV); HEX_REG_ALIAS_USR_NEW = ((REGFIELD(HEX_RF_WIDTH, HEX_REG_FIELD_USR_LPCFG)) ? deposit64(HEX_REG_ALIAS_USR_NEW, (REGFIELD(HEX_RF_OFFSET, HEX_REG_FIELD_USR_LPCFG)), (REGFIELD(HEX_RF_WIDTH, HEX_REG_FIELD_USR_LPCFG)), (((0)))) : HEX_REG_ALIAS_USR_NEW); }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_L2_loadrd_io(self):
        behavior = "{(siV);         EA = RsV + siV;    ; RddV = (size8u_t)(mem_load_u64(EA)); }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_storeri_io(self):
        behavior = "{(siV);         EA = RsV + siV;    ; mem_store_u32(EA, RtV); }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_storerd_io(self):
        behavior = "{(siV);         EA = RsV + siV;    ; mem_store_u64(EA, RttV); }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_L4_return(self):
        behavior = "{ size8u_t tmp;  EA = (RsV); ; tmp = (size8u_t)(mem_load_u64(EA)); RddV = ((tmp) ^ (((uint64_t)((HEX_REG_ALIAS_FRAMEKEY))) << 32)); (HEX_REG_ALIAS_SP = EA+8); JUMP(((int64_t)((int32_t)((RddV >> ((1) * 32)) & 0x0ffffffffLL))));}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S4_storeiri_io(self):
        behavior = "{        EA = RsV + uiV;    ; (SiV); mem_store_u32(EA, SiV); }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_cmpgtu(self):
        behavior = "{PdV=((((uint32_t)(RsV))>((uint32_t)(RtV))) ? 0xff : 0x00);}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_cmpgti(self):
        behavior = "{(siV); PdV=((RsV>siV) ? 0xff : 0x00);}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_xor(self):
        behavior = "{PdV=PsV ^ PtV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_C2_muxii(self):
        behavior = "{ (siV); RdV = (((PuV) & 1) ? siV : SiV); }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_M2_mpyi(self):
        behavior = "{ RdV=RsV*RtV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_sub(self):
        behavior = "{ RdV=RtV-RsV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_paddfnew(self):
        behavior = "{if((!((PuN) & 1))){RdV=RsV+RtV;} else {cancel_slot;}}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_psubfnew(self):
        behavior = "{if((!((PuN) & 1))){RdV=RtV-RsV;} else {cancel_slot;}}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_paddit(self):
        behavior = "{if(((PuV) & 1)){(siV); RdV=RsV+siV;} else {cancel_slot;}}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_addi(self):
        behavior = "{ (siV); RdV=RsV+siV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_abs(self):
        behavior = "{ RdV = (((RsV) < 0) ? (-(RsV)) : (RsV)); }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_nop(self):
        behavior = "{ }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A4_ext(self):
        behavior = "{ ; }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_tfr(self):
        behavior = "{ RdV=RsV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_tfrsi(self):
        behavior = "{ (siV); RdV=siV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_combinew(self):
        behavior = "{         RddV = (RddV & ~(0x0ffffffffLL << ((0) * 32))) |              (((RtV) & 0x0ffffffffLL) << ((0) * 32));    ;         RddV = (RddV & ~(0x0ffffffffLL << ((1) * 32))) |              (((RsV) & 0x0ffffffffLL) << ((1) * 32));    ; }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_combineii(self):
        behavior = "{ (siV);         RddV = (RddV & ~(0x0ffffffffLL << ((0) * 32))) |              (((SiV) & 0x0ffffffffLL) << ((0) * 32));    ;         RddV = (RddV & ~(0x0ffffffffLL << ((1) * 32))) |              (((siV) & 0x0ffffffffLL) << ((1) * 32));    ; }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_A2_subri(self):
        behavior = "{ (siV); RdV=siV-RsV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_lsr_i_vw(self):
        behavior = "{ int i; for (i=0;i<2;i++) {         RddV = (RddV & ~(0x0ffffffffLL << ((i) * 32))) |              ((((((uint64_t)((uint32_t)((RssV >> ((i) * 32)) & 0x0ffffffffLL)))>>uiV)) & 0x0ffffffffLL) << ((i) * 32));    ; } }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_lsl_r_vw(self):
        behavior = "{ int i; for (i=0;i<2;i++) {         RddV = (RddV & ~(0x0ffffffffLL << ((i) * 32))) |              (((((((((7) != 0) ? sextract64((RtV), 0, (7)) : 0LL)) < 0) ? ((((uint64_t)((uint32_t)(((uint64_t)((uint32_t)((RssV >> ((i) * 32)) & 0x0ffffffffLL)))))) >> ((-((((7) != 0) ? sextract64((RtV), 0, (7)) : 0LL))) - 1)) >> 1)                   : (((uint64_t)((uint32_t)(((uint64_t)((uint32_t)((RssV >> ((i) * 32)) & 0x0ffffffffLL)))))) << ((((7) != 0) ? sextract64((RtV), 0, (7)) : 0LL))))) & 0x0ffffffffLL) << ((i) * 32));    ; } }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_S2_cl0(self):
        behavior = "{RdV = clo32(~RsV);}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_addi(self):
        behavior = "{ (siV); RxV=RxV+siV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_tfr(self):
        behavior = "{ RdV=RsV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_seti(self):
        behavior = "{ (uiV); RdV=uiV;}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_combinezr(self):
        behavior = "{         RddV = (RddV & ~(0x0ffffffffLL << ((0) * 32))) |              (((RsV) & 0x0ffffffffLL) << ((0) * 32));    ;         RddV = (RddV & ~(0x0ffffffffLL << ((1) * 32))) |              (((0) & 0x0ffffffffLL) << ((1) * 32));    ; }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SA1_combine1i(self):
        behavior = "{         RddV = (RddV & ~(0x0ffffffffLL << ((0) * 32))) |              (((uiV) & 0x0ffffffffLL) << ((0) * 32));    ;         RddV = (RddV & ~(0x0ffffffffLL << ((1) * 32))) |              (((1) & 0x0ffffffffLL) << ((1) * 32));    ; }"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL1_loadri_io(self):
        behavior = "{        EA = RsV + uiV;    ; RdV = (size4u_t)(mem_load_u32(EA));}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_loadrh_io(self):
        behavior = "{        EA = RsV + uiV;    ; RdV = (size2s_t)(mem_load_s16(EA));}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_loadrd_sp(self):
        behavior = "{        EA = (HEX_REG_ALIAS_SP) + uiV;    ; RddV = (size8u_t)(mem_load_u64(EA));}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SL2_jumpr31_t(self):
        behavior = "{; if (((P0(self)) & 1)) {JUMP((HEX_REG_ALIAS_LR));}}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_storeh_io(self):
        behavior = "{        EA = RsV + uiV;    ; mem_store_u16(EA, ((int16_t)((RtV >> ((0) * 16)) & 0xffff)));}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_stored_sp(self):
        behavior = "{        EA = (HEX_REG_ALIAS_SP) + siV;    ; mem_store_u64(EA, RttV);}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_storew_sp(self):
        behavior = "{        EA = (HEX_REG_ALIAS_SP) + uiV;    ; mem_store_u32(EA, RtV);}"
        exc = self.compile_behavior(behavior)
        self.assertIsNone(exc)

    def test_SS2_allocframe(self):
        behavior = "{         EA = (HEX_REG_ALIAS_SP) + -8;    ; mem_store_u64(EA, (((((uint64_t)((HEX_REG_ALIAS_LR))) << 32) | ((uint32_t)((HEX_REG_ALIAS_FP)))) ^ (((uint64_t)((HEX_REG_ALIAS_FRAMEKEY))) << 32))); (HEX_REG_ALIAS_FP = EA); ; (HEX_REG_ALIAS_SP = EA-uiV); }"
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
