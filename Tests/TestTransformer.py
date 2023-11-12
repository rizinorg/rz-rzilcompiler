#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import logging
import re
import unittest

from Compiler import RZILInstruction, Compiler
from rzil_compiler.Transformer.Hybrids.SubRoutine import SubRoutine, SubRoutineInitType
from rzil_compiler.Transformer.Pures.Parameter import get_parameter_by_decl, Parameter
from rzil_compiler.Transformer.ValueType import (
    get_value_type_by_c_type,
    ValueType,
    VTGroup,
)
from rzil_compiler.Transformer.Pures.Register import Register
from rzil_compiler.Transformer.Pures.Cast import Cast
from rzil_compiler.Transformer.Pures.Number import Number
from rzil_compiler.Configuration import Conf, InputFile
from rzil_compiler.Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
from rzil_compiler.Transformer.RZILTransformer import RZILTransformer, CodeFormat
from rzil_compiler.ArchEnum import ArchEnum

from lark import Lark, logger
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


class TestTransformedInstr(unittest.TestCase):
    debug = False

    def test_set_get_item(self):
        instr = RZILInstruction("", [""], [[""]], [""])
        instr["aaaa"] = []
        self.assertListEqual(instr["aaaa"], [])

    def test_unimplemented(self):
        instr = RZILInstruction.get_unimplemented_rzil_instr("dummy")
        self.assertListEqual(instr["rzil"], ["NOT_IMPLEMENTED;"])
        self.assertListEqual(instr["meta"], [["HEX_IL_INSN_ATTR_INVALID"]])
        self.assertEqual(instr["getter_rzil"]["name"], ["hex_il_op_dummy"])
        self.assertEqual(
            instr["getter_rzil"]["fcn_decl"],
            ["RzILOpEffect *hex_il_op_dummy(HexInsnPktBundle *bundle)"],
        )

    def test_two_parts(self):
        instr = RZILInstruction(
            "dummy", ["aaa", "bbb"], [["ATTR_A"], ["ATTR_B"]], ["", ""]
        )
        self.assertListEqual(instr["rzil"], ["aaa", "bbb"])
        self.assertListEqual(instr["meta"], [["ATTR_A"], ["ATTR_B"]])
        self.assertEqual(
            instr["getter_rzil"]["name"],
            ["hex_il_op_dummy_part0", "hex_il_op_dummy_part1"],
        )
        self.assertEqual(
            instr["getter_rzil"]["fcn_decl"],
            [
                "RzILOpEffect *hex_il_op_dummy_part0(HexInsnPktBundle *bundle)",
                "RzILOpEffect *hex_il_op_dummy_part1(HexInsnPktBundle *bundle)",
            ],
        )

    def test_one_parts(self):
        instr = RZILInstruction("dummy", ["aaa"], [["ATTR_A"]], [""])
        self.assertListEqual(instr["rzil"], ["aaa"])
        self.assertListEqual(instr["meta"], [["ATTR_A"]])
        self.assertEqual(instr["getter_rzil"]["name"], ["hex_il_op_dummy"])
        self.assertEqual(
            instr["getter_rzil"]["fcn_decl"],
            ["RzILOpEffect *hex_il_op_dummy(HexInsnPktBundle *bundle)"],
        )

    def test_needs_var(self):
        instr = RZILInstruction(
            "dummy",
            [" hi pkt ", " hi ", " pkt ", ""],
            [[""], [""], [""], [""]],
            ["", "", "", ""],
        )
        self.assertTrue(instr["needs_hi"][0])
        self.assertTrue(instr["needs_pkt"][0])
        self.assertTrue(instr["needs_hi"][1])
        self.assertFalse(instr["needs_pkt"][1])
        self.assertFalse(instr["needs_hi"][2])
        self.assertTrue(instr["needs_pkt"][2])
        self.assertFalse(instr["needs_hi"][3])
        self.assertFalse(instr["needs_pkt"][3])


class TestTransforming(unittest.TestCase):
    debug = False
    insn_behavior: dict[str:tuple] = dict()

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = 1300
        cls.insn_behavior = get_hexagon_insn_behavior()
        cls.parser = get_hexagon_parser()
        cls.compiler = Compiler(ArchEnum.HEXAGON, code_format=CodeFormat.EXEC_CLASSES)

    def compile_behavior(
        self, behavior: str, transformer: RZILTransformer = None
    ) -> Exception | str:
        exception = None
        try:
            tree = self.parser.parse(behavior)
            if transformer:
                return transformer.transform(tree)
            else:
                transformer = RZILTransformer(
                    ArchEnum.HEXAGON,
                    sub_routines=self.compiler.sub_routines,
                    parameters=[
                        Parameter("pkt", get_value_type_by_c_type("HexPkt")),
                        Parameter("hi", get_value_type_by_c_type("HexInsn")),
                        Parameter(
                            "bundle", get_value_type_by_c_type("HexInsnPktBundle")
                        ),
                    ],
                    return_type=ValueType(False, 32, VTGroup.EXTERNAL, "RzILOpEffect"),
                    code_format=CodeFormat.EXEC_CLASSES,
                    macros=self.compiler.transformer.macros,
                )
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
        return exception

    def test_sub_routine(self):
        ret_val = get_value_type_by_c_type("uint64_t")
        params = [
            get_parameter_by_decl(p)
            for p in ["uint64_t value", "int start", "int length"]
        ]
        behavior = "{ return (value >> start) & (~0ULL >> (64 - length)); }"
        transformer = RZILTransformer(
            ArchEnum.HEXAGON,
            parameters=params,
            return_type=ret_val,
            code_format=CodeFormat.EXEC_CLASSES,
        )
        result = self.compile_behavior(behavior, transformer)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_storerinew_io(self):
        behavior = self.insn_behavior["S2_storerinew_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A4_cround_ri(self):
        behavior = self.insn_behavior["A4_cround_ri"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J2_jump(self):
        behavior = self.insn_behavior["J2_jump"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J2_jumpr(self):
        behavior = self.insn_behavior["J2_jumpr"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_M4_vpmpyh(self):
        behavior = self.insn_behavior["M4_vpmpyh"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_pstorerbnewt_io(self):
        behavior = self.insn_behavior["S2_pstorerbnewt_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J2_jumpt(self):
        behavior = self.insn_behavior["J2_jumpt"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J2_jumpf(self):
        behavior = self.insn_behavior["J2_jumpf"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J2_jumprt(self):
        behavior = self.insn_behavior["J2_jumprt"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J2_jumprf(self):
        behavior = self.insn_behavior["J2_jumprf"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J4_cmpgti_tp0_jump_t(self):
        behavior = self.insn_behavior["J4_cmpgti_tp0_jump_t"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

        behavior = self.insn_behavior["J4_cmpgti_tp0_jump_t"][1]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J2_call(self):
        behavior = self.insn_behavior["J2_call"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_J2_loop0r(self):
        behavior = self.insn_behavior["J2_loop0r"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_L2_loadrd_io(self):
        behavior = self.insn_behavior["L2_loadrd_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_storeri_io(self):
        behavior = self.insn_behavior["S2_storeri_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_storerd_io(self):
        behavior = self.insn_behavior["S2_storerd_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_L4_return(self):
        behavior = self.insn_behavior["L4_return"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S4_storeiri_io(self):
        behavior = self.insn_behavior["S4_storeiri_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_C2_cmpgtu(self):
        behavior = self.insn_behavior["C2_cmpgtu"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_C2_cmpgti(self):
        behavior = self.insn_behavior["C2_cmpgti"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_C2_xor(self):
        behavior = self.insn_behavior["C2_xor"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_C2_muxii(self):
        behavior = self.insn_behavior["C2_muxii"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_R6_release_at_vi(self):
        behavior = self.insn_behavior["R6_release_at_vi"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_L2_loadalignh_pci(self):
        behavior = self.insn_behavior["L2_loadalignh_pci"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_M2_mpyi(self):
        behavior = self.insn_behavior["M2_mpyi"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_sub(self):
        behavior = self.insn_behavior["A2_sub"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_paddfnew(self):
        behavior = self.insn_behavior["A2_paddfnew"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_psubfnew(self):
        behavior = self.insn_behavior["A2_psubfnew"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_paddit(self):
        behavior = self.insn_behavior["A2_paddit"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_addi(self):
        behavior = self.insn_behavior["A2_addi"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_abs(self):
        behavior = self.insn_behavior["A2_abs"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_nop(self):
        behavior = self.insn_behavior["A2_nop"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A4_ext(self):
        behavior = self.insn_behavior["A4_ext"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_tfr(self):
        behavior = self.insn_behavior["A2_tfr"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_tfrsi(self):
        behavior = self.insn_behavior["A2_tfrsi"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_vavgwcr(self):
        behavior = self.insn_behavior["A2_vavgwcr"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_combinew(self):
        behavior = self.insn_behavior["A2_combinew"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_combineii(self):
        behavior = self.insn_behavior["A2_combineii"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_subri(self):
        behavior = self.insn_behavior["A2_subri"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_lsr_i_vw(self):
        behavior = self.insn_behavior["S2_lsr_i_vw"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_lsl_r_vw(self):
        behavior = self.insn_behavior["S2_lsl_r_vw"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_cl0(self):
        behavior = self.insn_behavior["S2_cl0"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SA1_addi(self):
        behavior = self.insn_behavior["SA1_addi"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SA1_tfr(self):
        behavior = self.insn_behavior["SA1_tfr"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SA1_seti(self):
        behavior = self.insn_behavior["SA1_seti"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SA1_combinezr(self):
        behavior = self.insn_behavior["SA1_combinezr"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SA1_combine1i(self):
        behavior = self.insn_behavior["SA1_combine1i"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SL1_loadri_io(self):
        behavior = self.insn_behavior["SL1_loadri_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SL2_loadrh_io(self):
        behavior = self.insn_behavior["SL2_loadrh_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SL2_loadrd_sp(self):
        behavior = self.insn_behavior["SL2_loadrd_sp"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SL2_jumpr31_t(self):
        behavior = self.insn_behavior["SL2_jumpr31_t"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SS2_storeh_io(self):
        behavior = self.insn_behavior["SS2_storeh_io"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SS2_stored_sp(self):
        behavior = self.insn_behavior["SS2_stored_sp"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SS2_storew_sp(self):
        behavior = self.insn_behavior["SS2_storew_sp"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_SS2_allocframe(self):
        behavior = self.insn_behavior["SS2_allocframe"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_cl0p(self):
        behavior = self.insn_behavior["S2_cl0p"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_F2_sfadd(self):
        behavior = self.insn_behavior["F2_sfadd"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_addpsat(self):
        behavior = self.insn_behavior["A2_addpsat"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_vcrotate(self):
        behavior = self.insn_behavior["S2_vcrotate"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_S2_storerigp(self):
        behavior = self.insn_behavior["S2_storerigp"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))

    def test_A2_abs_syntax(self):
        behavior = self.insn_behavior["A2_abs"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))
        self.assertEqual(
            """
            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', false);
            const HexOp *Rs_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);

            // EXEC
            RzILOpPure *op_LT_3 = SLT(Rs, SN(32, 0));
            RzILOpPure *op_NEG_4 = NEG(DUP(Rs));
            RzILOpPure *cond_5 = ITE(op_LT_3, op_NEG_4, DUP(Rs));

            // WRITE
            RzILOpEffect *op_ASSIGN_6 = WRITE_REG(bundle, Rd_op, cond_5);
            RzILOpEffect *instruction_sequence = op_ASSIGN_6;

            return instruction_sequence;""".replace(
                "  ", ""
            ),
            result,
        )

    def test_size_t(self):
        behavior = "{ size8u_t a = 0x0; uint64_t b = (size8u_t) 0x1; }"
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))
        self.assertEqual(
            """
            // READ
            // Declare: ut64 a;
            // Declare: ut64 b;

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_2 = SETL("a", CAST(64, IL_FALSE, SN(32, 0)));
            RzILOpEffect *op_ASSIGN_7 = SETL("b", CAST(64, IL_FALSE, SN(32, 1)));
            RzILOpEffect *instruction_sequence = SEQN(2, op_ASSIGN_2, op_ASSIGN_7);

            return instruction_sequence;""".replace(
                "  ", ""
            ),
            result,
        )


class TestStmtEmitting(unittest.TestCase):
    insn_behavior: dict[str:tuple] = dict()

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = 2500
        cls.insn_behavior = get_hexagon_insn_behavior()
        cls.parser = get_hexagon_parser()
        cls.compiler = Compiler(ArchEnum.HEXAGON)

    def compile_behavior(
        self, behavior: str, transformer: RZILTransformer = None
    ) -> str:
        tree = self.parser.parse(behavior)
        if transformer:
            return transformer.transform(tree)
        else:
            transformer = RZILTransformer(
                ArchEnum.HEXAGON,
                sub_routines=self.compiler.sub_routines,
                parameters=[
                    Parameter("pkt", get_value_type_by_c_type("HexPkt")),
                    Parameter("hi", get_value_type_by_c_type("HexInsn")),
                    Parameter("bundle", get_value_type_by_c_type("HexInsnPktBundle")),
                ],
                return_type=ValueType(False, 32, VTGroup.EXTERNAL, "RzILOpEffect"),
                macros=self.compiler.transformer.macros,
            )
            return transformer.transform(tree)

    def test_C2_mask(self):
        behavior = self.insn_behavior["C2_mask"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))
        self.assertEqual(
            """
        // READ
        // Declare: st32 i;
        const HexOp *Rdd_op = ISA2REG(hi, 'd', false);
        const HexOp *Pt_op = ISA2REG(hi, 't', false);
        RzILOpPure *Pt = READ_REG(pkt, Pt_op, false);

        // i = 0x0;
        RzILOpEffect *op_ASSIGN_2 = SETL("i", SN(32, 0));

        // HYB(++i);
        RzILOpEffect *op_INC_5 = SETL("i", INC(VARL("i"), 32));

        // h_tmp0 = HYB(++i);
        RzILOpEffect *op_ASSIGN_hybrid_tmp_6 = SETL("h_tmp0", VARL("i"));

        // seq(h_tmp0 = HYB(++i); HYB(++i));
        RzILOpEffect *seq_7 = SEQN(2, op_ASSIGN_hybrid_tmp_6, op_INC_5);

        // Rdd = ((st64) ((ut64) Rdd & ~0xff << i * 0x8) | ((ut64) ((st64) (((st32) Pt >> i) & 0x1 ? 0xff : 0x0)) & 0xff) << i * 0x8);
        RzILOpPure *op_MUL_11 = MUL(VARL("i"), SN(32, 8));
        RzILOpPure *op_LSHIFT_12 = SHIFTL0(SN(64, 0xff), op_MUL_11);
        RzILOpPure *op_NOT_13 = LOGNOT(op_LSHIFT_12);
        RzILOpPure *op_AND_14 = LOGAND(READ_REG(pkt, Rdd_op, true), op_NOT_13);
        RzILOpPure *op_RSHIFT_16 = SHIFTR0(Pt, VARL("i"));
        RzILOpPure *op_AND_19 = LOGAND(CAST(32, MSB(op_RSHIFT_16), DUP(op_RSHIFT_16)), SN(32, 1));
        RzILOpPure *cond_22 = ITE(NON_ZERO(op_AND_19), SN(32, 0xff), SN(32, 0));
        RzILOpPure *op_AND_25 = LOGAND(CAST(64, MSB(cond_22), DUP(cond_22)), SN(64, 0xff));
        RzILOpPure *op_MUL_28 = MUL(VARL("i"), SN(32, 8));
        RzILOpPure *op_LSHIFT_29 = SHIFTL0(CAST(64, IL_FALSE, op_AND_25), op_MUL_28);
        RzILOpPure *op_OR_31 = LOGOR(CAST(64, IL_FALSE, op_AND_14), op_LSHIFT_29);
        RzILOpEffect *op_ASSIGN_33 = WRITE_REG(bundle, Rdd_op, CAST(64, MSB(op_OR_31), DUP(op_OR_31)));

        // seq(h_tmp0; Rdd = ((st64) ((ut64) Rdd & ~0xff << i * 0x8) | ((ut ...;
        RzILOpEffect *seq_35 = SEQN(2, op_ASSIGN_33, EMPTY());

        // seq(seq(h_tmp0 = HYB(++i); HYB(++i)); seq(h_tmp0; Rdd = ((st64)  ...;
        RzILOpEffect *seq_36 = SEQN(2, seq_7, seq_35);

        // while (i < 0x8) { seq(seq(h_tmp0 = HYB(++i); HYB(++i)); seq(h_tmp0; Rdd = ((st64)  ... };
        RzILOpPure *op_LT_4 = SLT(VARL("i"), SN(32, 8));
        RzILOpEffect *for_37 = REPEAT(op_LT_4, seq_36);

        // seq(i = 0x0; while (i < 0x8) { seq(seq(h_tmp0 = HYB(++i); HYB(++ ...;
        RzILOpEffect *seq_38 = SEQN(2, op_ASSIGN_2, for_37);

        RzILOpEffect *instruction_sequence = seq_38;
        return instruction_sequence;""".replace(
                "  ", ""
            ),
            result,
        )

    def test_A4_tlbmatch(self):
        behavior = self.insn_behavior["A4_tlbmatch"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))
        self.assertEqual(
            """
            // READ
            // Declare: ut32 TLBHI;
            // Declare: ut32 TLBLO;
            // Declare: ut32 MASK;
            // Declare: ut32 SIZE;
            const HexOp *Rss_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rss = READ_REG(pkt, Rss_op, false);
            const HexOp *Pd_op = ISA2REG(hi, 'd', false);
            const HexOp *Rt_op = ISA2REG(hi, 't', false);
            RzILOpPure *Rt = READ_REG(pkt, Rt_op, false);

            // MASK = ((ut32) 0x7ffffff);
            RzILOpEffect *op_ASSIGN_6 = SETL("MASK", CAST(32, IL_FALSE, SN(32, 0x7ffffff)));

            // TLBLO = ((ut32) ((ut64) ((ut32) Rss >> 0x0 & 0xffffffff)));
            RzILOpPure *op_RSHIFT_11 = SHIFTR0(Rss, SN(32, 0));
            RzILOpPure *op_AND_13 = LOGAND(op_RSHIFT_11, SN(64, 0xffffffff));
            RzILOpEffect *op_ASSIGN_17 = SETL("TLBLO", CAST(32, IL_FALSE, CAST(64, IL_FALSE, CAST(32, IL_FALSE, op_AND_13))));

            // TLBHI = ((ut32) ((ut64) ((ut32) Rss >> 0x20 & 0xffffffff)));
            RzILOpPure *op_RSHIFT_21 = SHIFTR0(DUP(Rss), SN(32, 0x20));
            RzILOpPure *op_AND_23 = LOGAND(op_RSHIFT_21, SN(64, 0xffffffff));
            RzILOpEffect *op_ASSIGN_27 = SETL("TLBHI", CAST(32, IL_FALSE, CAST(64, IL_FALSE, CAST(32, IL_FALSE, op_AND_23))));

            // HYB(None_TLBLO);
            RzILOpEffect *revbit32_call_29 = hex_revbit32(VARL("TLBLO"));

            // h_tmp0 = HYB(None_TLBLO);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_30 = SETL("h_tmp0", UNSIGNED(32, VARL("ret_val")));

            // seq(HYB(None_TLBLO); h_tmp0 = HYB(None_TLBLO));
            RzILOpEffect *seq_31 = SEQN(2, revbit32_call_29, op_ASSIGN_hybrid_tmp_30);

            // HYB(None_~h_tmp0);
            RzILOpPure *op_NOT_32 = LOGNOT(VARL("h_tmp0"));
            RzILOpEffect *clo32_call_33 = hex_clo32(op_NOT_32);

            // h_tmp1 = HYB(None_~h_tmp0);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_34 = SETL("h_tmp1", UNSIGNED(32, VARL("ret_val")));

            // seq(HYB(None_~h_tmp0); h_tmp1 = HYB(None_~h_tmp0));
            RzILOpEffect *seq_35 = SEQN(2, clo32_call_33, op_ASSIGN_hybrid_tmp_34);

            // seq(seq(HYB(None_TLBLO); h_tmp0 = HYB(None_TLBLO)); seq(HYB(None ...;
            RzILOpEffect *seq_36 = SEQN(2, seq_31, seq_35);

            // HYB(None_TLBLO);
            RzILOpEffect *revbit32_call_40 = hex_revbit32(VARL("TLBLO"));

            // h_tmp2 = HYB(None_TLBLO);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_41 = SETL("h_tmp2", UNSIGNED(32, VARL("ret_val")));

            // seq(HYB(None_TLBLO); h_tmp2 = HYB(None_TLBLO));
            RzILOpEffect *seq_42 = SEQN(2, revbit32_call_40, op_ASSIGN_hybrid_tmp_41);

            // HYB(None_~h_tmp2);
            RzILOpPure *op_NOT_43 = LOGNOT(VARL("h_tmp2"));
            RzILOpEffect *clo32_call_44 = hex_clo32(op_NOT_43);

            // h_tmp3 = HYB(None_~h_tmp2);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_45 = SETL("h_tmp3", UNSIGNED(32, VARL("ret_val")));

            // seq(HYB(None_~h_tmp2); h_tmp3 = HYB(None_~h_tmp2));
            RzILOpEffect *seq_46 = SEQN(2, clo32_call_44, op_ASSIGN_hybrid_tmp_45);

            // seq(seq(HYB(None_TLBLO); h_tmp2 = HYB(None_TLBLO)); seq(HYB(None ...;
            RzILOpEffect *seq_47 = SEQN(2, seq_42, seq_46);

            // SIZE = (((ut32) 0x6) < h_tmp1 ? ((ut32) 0x6) : h_tmp3);
            RzILOpPure *op_LT_38 = ULT(CAST(32, IL_FALSE, SN(32, 6)), VARL("h_tmp1"));
            RzILOpPure *cond_49 = ITE(op_LT_38, CAST(32, IL_FALSE, SN(32, 6)), VARL("h_tmp3"));
            RzILOpEffect *op_ASSIGN_50 = SETL("SIZE", cond_49);

            // seq(seq(seq(HYB(None_TLBLO); h_tmp0 = HYB(None_TLBLO)); seq(HYB( ...;
            RzILOpEffect *seq_51 = SEQN(3, seq_36, seq_47, op_ASSIGN_50);

            // MASK = MASK & ((ut32) 0xffffffff << ((ut32) 0x2) * SIZE);
            RzILOpPure *op_MUL_55 = MUL(CAST(32, IL_FALSE, SN(32, 2)), VARL("SIZE"));
            RzILOpPure *op_LSHIFT_56 = SHIFTL0(SN(32, 0xffffffff), op_MUL_55);
            RzILOpPure *op_AND_58 = LOGAND(VARL("MASK"), CAST(32, IL_FALSE, op_LSHIFT_56));
            RzILOpEffect *op_ASSIGN_AND_59 = SETL("MASK", op_AND_58);

            // Pd = ((st8) (TLBHI >> 0x1f & ((ut32) 0x1) && TLBHI & MASK == ((ut32) Rt) & MASK ? 0xff : 0x0));
            RzILOpPure *op_RSHIFT_62 = SHIFTR0(VARL("TLBHI"), SN(32, 31));
            RzILOpPure *op_AND_65 = LOGAND(op_RSHIFT_62, CAST(32, IL_FALSE, SN(32, 1)));
            RzILOpPure *op_AND_66 = LOGAND(VARL("TLBHI"), VARL("MASK"));
            RzILOpPure *op_AND_69 = LOGAND(CAST(32, IL_FALSE, Rt), VARL("MASK"));
            RzILOpPure *op_EQ_70 = EQ(op_AND_66, op_AND_69);
            RzILOpPure *op_AND_71 = AND(NON_ZERO(op_AND_65), op_EQ_70);
            RzILOpPure *cond_74 = ITE(op_AND_71, SN(32, 0xff), SN(32, 0));
            RzILOpEffect *op_ASSIGN_76 = WRITE_REG(bundle, Pd_op, CAST(8, MSB(cond_74), DUP(cond_74)));

            RzILOpEffect *instruction_sequence = SEQN(6, op_ASSIGN_6, op_ASSIGN_17, op_ASSIGN_27, seq_51, op_ASSIGN_AND_59, op_ASSIGN_76);
            return instruction_sequence;""".replace(
                "  ", ""
            ),
            result,
        )

    def test_S2_lsl_r_p(self):
        behavior = self.insn_behavior["S2_lsl_r_p"][0]
        result = self.compile_behavior(behavior)
        self.assertFalse(isinstance(result, Exception))
        self.assertEqual(
            """
            // READ
            const HexOp *Rt_op = ISA2REG(hi, 't', false);
            RzILOpPure *Rt = READ_REG(pkt, Rt_op, false);
            // Declare: st32 shamt;
            const HexOp *Rdd_op = ISA2REG(hi, 'd', false);
            const HexOp *Rss_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rss = READ_REG(pkt, Rss_op, false);

            // sextract64(((ut64) Rt), 0x0, 0x7);
            RzILOpEffect *sextract64_call_7 = hex_sextract64(CAST(64, IL_FALSE, Rt), SN(32, 0), SN(32, 7));

            // h_tmp0 = sextract64(((ut64) Rt), 0x0, 0x7);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_8 = SETL("h_tmp0", SIGNED(64, VARL("ret_val")));

            // seq(sextract64(((ut64) Rt), 0x0, 0x7); h_tmp0 = sextract64(((ut6 ...;
            RzILOpEffect *seq_9 = SEQN(2, sextract64_call_7, op_ASSIGN_hybrid_tmp_8);

            // shamt = ((st32) (0x7 != 0x0 ? h_tmp0 : 0x0));
            RzILOpPure *op_NE_2 = INV(EQ(SN(32, 7), SN(32, 0)));
            RzILOpPure *cond_11 = ITE(op_NE_2, VARL("h_tmp0"), SN(64, 0));
            RzILOpEffect *op_ASSIGN_13 = SETL("shamt", CAST(32, MSB(cond_11), DUP(cond_11)));

            // seq(seq(sextract64(((ut64) Rt), 0x0, 0x7); h_tmp0 = sextract64(( ...;
            RzILOpEffect *seq_14 = SEQN(2, seq_9, op_ASSIGN_13);

            // Rdd = ((st64) (shamt < 0x0 ? ((ut64) Rss) >> -shamt - 0x1 >> 0x1 : ((ut64) Rss) << shamt));
            RzILOpPure *op_LT_18 = SLT(VARL("shamt"), SN(32, 0));
            RzILOpPure *op_NEG_21 = NEG(VARL("shamt"));
            RzILOpPure *op_SUB_23 = SUB(op_NEG_21, SN(32, 1));
            RzILOpPure *op_RSHIFT_24 = SHIFTR0(CAST(64, IL_FALSE, Rss), op_SUB_23);
            RzILOpPure *op_RSHIFT_26 = SHIFTR0(op_RSHIFT_24, SN(32, 1));
            RzILOpPure *op_LSHIFT_28 = SHIFTL0(CAST(64, IL_FALSE, DUP(Rss)), VARL("shamt"));
            RzILOpPure *cond_29 = ITE(op_LT_18, op_RSHIFT_26, op_LSHIFT_28);
            RzILOpEffect *op_ASSIGN_31 = WRITE_REG(bundle, Rdd_op, CAST(64, MSB(cond_29), DUP(cond_29)));

            RzILOpEffect *instruction_sequence = SEQN(2, seq_14, op_ASSIGN_31);
            return instruction_sequence;""".replace(
                "  ", ""
            ),
            result,
        )


class TestTransformerMeta(unittest.TestCase):
    debug = False
    insn_behavior: dict[str:tuple] = dict()

    @classmethod
    def setUpClass(cls):
        cls.insn_behavior = get_hexagon_insn_behavior()
        cls.parser = get_hexagon_parser()
        cls.compiler = Compiler(ArchEnum.HEXAGON)

    def compile_behavior(self, behavior: str) -> list[str]:
        try:
            tree = self.parser.parse(behavior)
            transformer = RZILTransformer(
                ArchEnum.HEXAGON,
                sub_routines=self.compiler.sub_routines,
                parameters=[
                    Parameter("pkt", get_value_type_by_c_type("HexPkt")),
                    Parameter("hi", get_value_type_by_c_type("HexInsn")),
                    Parameter("bundle", get_value_type_by_c_type("HexInsnPktBundle")),
                ],
                return_type=ValueType(False, 32, VTGroup.EXTERNAL, "RzILOpEffect"),
                code_format=CodeFormat.EXEC_CLASSES,
                macros=self.compiler.transformer.macros,
            )
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
        cls.compiler = Compiler(ArchEnum.HEXAGON, code_format=CodeFormat.EXEC_CLASSES)
        cls.transformer = RZILTransformer(
            ArchEnum.HEXAGON, code_format=CodeFormat.EXEC_CLASSES
        )

    def get_new_transformer(self, formatting: CodeFormat = CodeFormat.EXEC_CLASSES):
        return RZILTransformer(
            ArchEnum.HEXAGON,
            code_format=formatting,
            sub_routines=self.compiler.transformer.sub_routines,
        )

    def compile_behavior(
        self, behavior: str, transformer: RZILTransformer = None
    ) -> list[str]:
        try:
            tree = self.parser.parse(behavior)
            if transformer:
                return transformer.transform(tree)
            else:
                self.transformer.reset()
                return self.transformer.transform(tree)
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
        raise exception

    def test_empty_stmt_is_empty(self):
        behavior = "{}"
        output = self.compile_behavior(behavior)
        expected = "RzILOpEffect *instruction_sequence = EMPTY();\n\nreturn instruction_sequence;"
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_sub_routines_with_external_types(self):
        self.maxDiff = 1000
        name = "test_routine"
        ret_type = get_value_type_by_c_type("uint64_t")
        params = [
            get_parameter_by_decl(p)
            for p in [
                "HexInsnPktBundle *bundle",
                "const HexOp *RdV",
                "int start",
                "const HexOp *RsV",
            ]
        ]
        code = "{ RdV = RsV + start; }"
        ast_body = self.parser.parse(code)
        body = RZILTransformer(
            ArchEnum.HEXAGON,
            parameters=params,
            return_type=ret_type,
            code_format=CodeFormat.EXEC_CLASSES,
        ).transform(ast_body)
        sub_routine = SubRoutine(name, ret_type, params, body)

        self.assertEqual(
            """RZ_OWN RzILOpEffect *hex_test_routine(HexInsnPktBundle *bundle, const HexOp *RdV, RZ_BORROW RzILOpPure *start, const HexOp *RsV){
            const HexInsn *hi = bundle->insn;
            HexPkt *pkt = bundle->pkt;

            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', false);
            const HexOp *Rs_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);

            // EXEC
            RzILOpPure *op_ADD_2 = ADD(Rs, start);

            // WRITE
            RzILOpEffect *op_ASSIGN_3 = WRITE_REG(bundle, Rd_op, op_ADD_2);
            RzILOpEffect *instruction_sequence = op_ASSIGN_3;

            return instruction_sequence;
        }""".replace(
                "  ", ""
            ),
            sub_routine.il_init(SubRoutineInitType.DEF),
        )

        ret_type = get_value_type_by_c_type("RzILOpEffect *")
        params = [
            get_parameter_by_decl(p)
            for p in [
                "HexInsnPktBundle *bundle",
            ]
        ]

        code = "{ hex_test_routine(bundle, RdV, 0x0, RsV); }"
        ast_body = self.parser.parse(code)
        body = RZILTransformer(
            ArchEnum.HEXAGON,
            parameters=params,
            return_type=ret_type,
            sub_routines={"hex_test_routine": sub_routine},
            code_format=CodeFormat.EXEC_CLASSES,
        ).transform(ast_body)

        self.assertEqual(
            """
            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', false);
            const HexOp *Rs_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);

            // EXEC

            // WRITE
            RzILOpEffect *test_routine_call_3 = hex_test_routine(bundle, Rd_op, SN(32, 0), Rs_op);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_5 = SETL("h_tmp0", UNSIGNED(64, VARL("ret_val")));
            RzILOpEffect *seq_6 = SEQN(2, test_routine_call_3, op_ASSIGN_hybrid_tmp_5);
            RzILOpEffect *instruction_sequence = seq_6;

            return instruction_sequence;""".replace(
                "  ", ""
            ),
            body,
        )

    def test_add_sub_routine(self):
        name = "sextract64"
        return_type = "int64_t"
        parameters = ["uint64_t value", "int start", "int length"]
        code = (
            "{ return ((int32_t)(value << (32 - length - start))) >> (32 - length); }"
        )
        sub_routine = self.compiler.compile_sub_routine(
            name, return_type, parameters, code
        )
        # Use sub-routine
        ast_body = self.parser.parse("{ RdV = sextract64(0, 0, 0); }")
        transformer = RZILTransformer(
            ArchEnum.HEXAGON,
            sub_routines={"sextract64": sub_routine},
            code_format=CodeFormat.EXEC_CLASSES,
        )
        result = transformer.transform(ast_body)
        self.assertEqual(
            """
            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', false);

            // EXEC

            // WRITE
            RzILOpEffect *sextract64_call_5 = hex_sextract64(CAST(64, IL_FALSE, SN(32, 0)), SN(32, 0), SN(32, 0));
            RzILOpEffect *op_ASSIGN_hybrid_tmp_7 = SETL("h_tmp0", SIGNED(64, VARL("ret_val")));
            RzILOpEffect *seq_8 = SEQN(2, sextract64_call_5, op_ASSIGN_hybrid_tmp_7);
            RzILOpEffect *op_ASSIGN_10 = WRITE_REG(bundle, Rd_op, CAST(32, MSB(VARL("h_tmp0")), VARL("h_tmp0")));
            RzILOpEffect *seq_11 = SEQN(2, seq_8, op_ASSIGN_10);
            RzILOpEffect *instruction_sequence = seq_11;

            return instruction_sequence;""".replace(
                "  ", ""
            ),
            result,
        )

    def test_sub_routines(self):
        ret_val = get_value_type_by_c_type("uint64_t")
        params = [
            get_parameter_by_decl(p)
            for p in ["uint64_t value", "int start", "int length"]
        ]
        behavior = "{ return (value >> start) & (~0ULL >> (64 - length)); }"
        transformer = RZILTransformer(
            ArchEnum.HEXAGON,
            parameters=params,
            return_type=ret_val,
            code_format=CodeFormat.EXEC_CLASSES,
        )
        output = self.compile_behavior(behavior, transformer)
        self.assertEqual(
            """
            // READ

            // EXEC
            RzILOpPure *op_RSHIFT_0 = SHIFTR0(value, start);
            RzILOpPure *op_SUB_4 = SUB(SN(32, 0x40), length);
            RzILOpPure *op_RSHIFT_5 = SHIFTR0(UN(64, -1), op_SUB_4);
            RzILOpPure *op_AND_6 = LOGAND(op_RSHIFT_0, op_RSHIFT_5);

            // WRITE
            RzILOpEffect *set_return_val_8 = SETL("ret_val", op_AND_6);
            RzILOpEffect *instruction_sequence = set_return_val_8;

            return instruction_sequence;""".replace(
                "  ", ""
            ),
            output,
        )

    def test_cast_simplification_1(self):
        self.transformer.inlined_pure_classes = ()
        behavior = "{ uint64_t a = ((uint64_t)(uint32_t)(uint8_t) 0); }"
        output = self.compile_behavior(behavior)
        expected = (
            "RzILOpPure *const_0_0 = SN(32, 0x0);\n"
            "// Declare: ut64 a;\n\n"
            "// EXEC\n"
            'RzILOpPure *cast_ut8_1 = LET("const_0_0", const_0_0, CAST(8, IL_FALSE, VARLP("const_0_0")));\n'
            "RzILOpPure *cast_ut64_3 = CAST(64, IL_FALSE, cast_ut8_1);"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_cast_simplification_2(self):
        behavior = "{ uint64_t a = ((int64_t)((int8_t)((int32_t) 0))); }"
        self.transformer.inlined_pure_classes = ()
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            RzILOpPure *const_0_0 = SN(32, 0x0);
            // Declare: ut64 a;

            // EXEC
            RzILOpPure *cast_st8_1 = LET("const_0_0", const_0_0, CAST(8, MSB(VARLP("const_0_0")), VARLP("const_0_0")));
            RzILOpPure *cast_st64_2 = CAST(64, MSB(cast_st8_1), DUP(cast_st8_1));
            RzILOpPure *cast_ut64_5 = CAST(64, IL_FALSE, cast_st64_2);

            // WRITE
            RzILOpEffect *op_ASSIGN_4 = SETL("a", cast_ut64_5);
            RzILOpEffect *instruction_sequence = op_ASSIGN_4;

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_cast_simplification_compares_conditionals_1(self):
        behavior = "{ (1 == 0 ? 2 : clz32(8)); }"
        self.compiler.transformer.code_format = CodeFormat.READ_STATEMENTS
        output = self.compiler.compile_c_stmt(behavior)
        expected = """
        // READ

        // clz32(((ut32) 0x8));
        RzILOpEffect *clz32_call_6 = hex_clz32(CAST(32, IL_FALSE, SN(32, 8)));

        // h_tmp0 = clz32(((ut32) 0x8));
        RzILOpEffect *op_ASSIGN_hybrid_tmp_8 = SETL("h_tmp0", UNSIGNED(32, VARL("ret_val")));

        // seq(clz32(((ut32) 0x8)); h_tmp0 = clz32(((ut32) 0x8)));
        RzILOpEffect *seq_9 = SEQN(2, clz32_call_6, op_ASSIGN_hybrid_tmp_8);

        RzILOpEffect *instruction_sequence = seq_9;
        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_cast_simplification_compares_conditionals_2(self):
        behavior = "{ int a = (1 == 0 ? clz32(8) : 2); }"
        self.compiler.transformer.code_format = CodeFormat.READ_STATEMENTS
        output = self.compiler.compile_c_stmt(behavior)
        expected = """
        // READ
        // Declare: st32 a;

        // a = 0x2;
        RzILOpEffect *op_ASSIGN_11 = SETL("a", SN(32, 2));

        RzILOpEffect *instruction_sequence = op_ASSIGN_11;
        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_simplify_arith_expr(self):
        # Simplify e.g. 4 - 1 = 3
        behavior = "{ uint32_t a = 1 + 1 * 7; }"
        output = self.compile_behavior(behavior)
        expected = (
            "// WRITE\n"
            'RzILOpEffect *op_ASSIGN_6 = SETL("a", CAST(32, IL_FALSE, SN(32, 8)));\n'
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_simplify_unary_expr_neg(self):
        # Simplify e.g. ~0x3
        behavior = "{ uint32_t a = ~0x3;  }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ
        // Declare: ut32 a;

        // EXEC

        // WRITE
        RzILOpEffect *op_ASSIGN_3 = SETL("a", CAST(32, IL_FALSE, SN(32, -4)));
        RzILOpEffect *instruction_sequence = op_ASSIGN_3;

        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_simplify_unary_expr_pm(self):
        behavior = "{ uint32_t a = +8 + - +5;  }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ
        // Declare: ut32 a;

        // EXEC

        // WRITE
        RzILOpEffect *op_ASSIGN_7 = SETL("a", CAST(32, IL_FALSE, SN(32, 3)));
        RzILOpEffect *instruction_sequence = op_ASSIGN_7;

        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_simplify_unary_expr_minus(self):
        behavior = "{ int32_t a = -(+0x3);  }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ
        // Declare: st32 a;

        // EXEC

        // WRITE
        RzILOpEffect *op_ASSIGN_4 = SETL("a", SN(32, -3));
        RzILOpEffect *instruction_sequence = op_ASSIGN_4;

        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_inlining_nothing(self):
        behavior = "{ int64_t a = 0; }"
        self.transformer.inlined_pure_classes = ()
        output = self.compile_behavior(behavior)
        expected = (
            "\n"
            "// READ\n"
            "RzILOpPure *const_0_0 = SN(32, 0x0);\n"
            "// Declare: st64 a;\n\n"
            "// EXEC\n"
            'RzILOpPure *cast_st64_3 = LET("const_0_0", const_0_0, CAST(64, MSB(VARLP("const_0_0")), VARLP("const_0_0")));\n\n'
            "// WRITE\n"
            'RzILOpEffect *op_ASSIGN_2 = SETL("a", cast_st64_3);\n'
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_inlining_number_only(self):
        behavior = "{ int64_t a = 0; }"
        self.transformer.inlined_pure_classes = Number
        output = self.compile_behavior(behavior)
        expected = (
            "// READ\n"
            "// Declare: st64 a;\n\n"
            "// EXEC\n"
            "RzILOpPure *cast_st64_3 = CAST(64, MSB(SN(32, 0)), SN(32, 0));\n\n"
            "// WRITE\n"
            'RzILOpEffect *op_ASSIGN_2 = SETL("a", cast_st64_3);\n'
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_inlining_casts_only(self):
        behavior = "{ int64_t a = 0; }"
        self.transformer.inlined_pure_classes = Cast
        output = self.compile_behavior(behavior)
        expected = (
            "\n"
            "// READ\n"
            "RzILOpPure *const_0_0 = SN(32, 0x0);\n"
            "// Declare: st64 a;\n\n"
            "// EXEC\n\n"
            "// WRITE\n"
            'RzILOpEffect *op_ASSIGN_2 = SETL("a", LET("const_0_0", const_0_0, CAST(64, MSB(VARLP("const_0_0")), VARLP("const_0_0"))));\n'
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_inlining_pure_exec_lp(self):
        behavior = "{ int64_t a = 0; }"
        self.transformer.inlined_pure_classes = (Cast, Number)
        output = self.compile_behavior(behavior)
        expected = (
            "\n"
            "// READ\n"
            "// Declare: st64 a;\n\n"
            "// EXEC\n\n"
            "// WRITE\n"
            'RzILOpEffect *op_ASSIGN_2 = SETL("a", CAST(64, MSB(SN(32, 0)), SN(32, 0)));\n'
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_store_cancelled_fcn(self):
        behavior = "{ STORE_SLOT_CANCELLED(pkt, slot); }"
        output = self.compile_behavior(behavior)
        expected = "RzILOpEffect *c_call_0 = HEX_STORE_SLOT_CANCELLED(pkt, hi->slot);\n"
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_reg_write(self):
        behavior = "{ RdV = 0x0; }"
        output = self.compile_behavior(behavior)
        expected = (
            "// READ\n"
            "const HexOp *Rd_op = ISA2REG(hi, 'd', false);\n\n"
            "// EXEC\n\n// WRITE\n"
            "RzILOpEffect *op_ASSIGN_2 = WRITE_REG(bundle, Rd_op, SN(32, 0));\n"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_set_usr_field(self):
        behavior = "{ set_usr_field(bundle, HEX_REG_FIELD_USR_OVF, 1); }"
        output = self.compile_behavior(behavior, self.get_new_transformer())
        expected = """
            // READ

            // EXEC

            // WRITE
            RzILOpEffect *set_usr_field_call_2 = hex_set_usr_field(bundle, HEX_REG_FIELD_USR_OVF, CAST(32, IL_FALSE, SN(32, 1)));
            RzILOpEffect *instruction_sequence = set_usr_field_call_2;

            return instruction_sequence;""".replace(
            "    ", ""
        )
        self.assertEqual(expected, output)

    def test_get_usr_field(self):
        behavior = "{ uint32_t f = get_usr_field(bundle, HEX_REG_FIELD_USR_OVF); }"
        output = self.compile_behavior(behavior, self.get_new_transformer())
        expected = """
            // READ
            // Declare: ut32 f;

            // EXEC

            // WRITE
            RzILOpEffect *get_usr_field_call_0 = hex_get_usr_field(bundle, HEX_REG_FIELD_USR_OVF);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_2 = SETL("h_tmp0", UNSIGNED(32, VARL("ret_val")));
            RzILOpEffect *seq_3 = SEQN(2, get_usr_field_call_0, op_ASSIGN_hybrid_tmp_2);
            RzILOpEffect *op_ASSIGN_5 = SETL("f", VARL("h_tmp0"));
            RzILOpEffect *seq_6 = SEQN(2, seq_3, op_ASSIGN_5);
            RzILOpEffect *instruction_sequence = seq_6;

            return instruction_sequence;""".replace(
            "    ", ""
        )
        self.assertEqual(expected, output)

    def test_reg_read(self):
        behavior = "{ RdV = RsV; }"
        output = self.compile_behavior(behavior)
        expected = (
            "// READ\n"
            "const HexOp *Rd_op = ISA2REG(hi, 'd', false);\n"
            "const HexOp *Rs_op = ISA2REG(hi, 's', false);\n"
            "RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);\n\n"
            "// EXEC\n\n// WRITE\n"
            "RzILOpEffect *op_ASSIGN_2 = WRITE_REG(bundle, Rd_op, Rs);\n"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_reg_read_write(self):
        behavior = "{ RxV = RxV; }"
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            const HexOp *Rx_op = ISA2REG(hi, 'x', false);
            RzILOpPure *Rx = READ_REG(pkt, Rx_op, false);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_1 = WRITE_REG(bundle, Rx_op, Rx);
            RzILOpEffect *instruction_sequence = op_ASSIGN_1;

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_reg_explicit_assign(self):
        behavior = "{ P1_NEW = P0; R11:10_NEW = C31:30; }"
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            const HexOp P1_new_op = EXPLICIT2OP(1, HEX_REG_CLASS_PRED_REGS, true);
            const HexOp P0_op = EXPLICIT2OP(0, HEX_REG_CLASS_PRED_REGS, false);
            RzILOpPure *P0 = READ_REG(pkt, &P0_op, false);
            const HexOp R11_10_new_op = EXPLICIT2OP(10, HEX_REG_CLASS_DOUBLE_REGS, true);
            const HexOp C31_30_op = EXPLICIT2OP(30, HEX_REG_CLASS_CTR_REGS64, false);
            RzILOpPure *C31_30 = READ_REG(pkt, &C31_30_op, false);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_2 = WRITE_REG(bundle, &P1_new_op, P0);
            RzILOpEffect *op_ASSIGN_5 = WRITE_REG(bundle, &R11_10_new_op, C31_30);
            RzILOpEffect *instruction_sequence = SEQN(2, op_ASSIGN_2, op_ASSIGN_5);

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_reg_explicit_new(self):
        behavior = "{ P0 = P0_NEW; }"
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            const HexOp P0_op = EXPLICIT2OP(0, HEX_REG_CLASS_PRED_REGS, false);
            const HexOp P0_new_op = EXPLICIT2OP(0, HEX_REG_CLASS_PRED_REGS, true);
            RzILOpPure *P0_new = READ_REG(pkt, &P0_new_op, true);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_2 = WRITE_REG(bundle, &P0_op, P0_new);
            RzILOpEffect *instruction_sequence = op_ASSIGN_2;

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_reg_alias_new(self):
        behavior = "{ HEX_REG_ALIAS_LR = HEX_REG_ALIAS_LR_NEW; }"
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            const HexOp lr_op = ALIAS2OP(HEX_REG_ALIAS_LR, false);
            const HexOp lr_new_op = ALIAS2OP(HEX_REG_ALIAS_LR, true);
            RzILOpPure *lr_new = READ_REG(pkt, &lr_new_op, true);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_2 = WRITE_REG(bundle, &lr_op, lr_new);
            RzILOpEffect *instruction_sequence = op_ASSIGN_2;

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_reg_gp(self):
        behavior = "{ HEX_REG_ALIAS_GP = 0; }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ
        const HexOp gp_op = ALIAS2OP(HEX_REG_ALIAS_GP, false);

        // EXEC

        // WRITE
        RzILOpEffect *op_ASSIGN_3 = WRITE_REG(bundle, &gp_op, CAST(32, IL_FALSE, SN(32, 0)));
        RzILOpEffect *instruction_sequence = op_ASSIGN_3;

        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_for_loop(self):
        behavior = "{ for (int i = 0; i < 2; i++) { __NOP; }; }"
        output = self.compile_behavior(behavior, self.get_new_transformer())
        expected = """
        // READ
        // Declare: st32 i;

        // EXEC
        RzILOpPure *op_LT_4 = SLT(VARL("i"), SN(32, 2));

        // WRITE
        RzILOpEffect *op_ASSIGN_2 = SETL("i", SN(32, 0));
        RzILOpEffect *op_INC_5 = SETL("i", INC(VARL("i"), 32));
        RzILOpEffect *op_ASSIGN_hybrid_tmp_7 = SETL("h_tmp0", VARL("i"));
        RzILOpEffect *seq_8 = SEQN(2, op_ASSIGN_hybrid_tmp_7, op_INC_5);
        RzILOpEffect *seq_9 = EMPTY();
        RzILOpEffect *seq_10 = SEQN(2, seq_9, seq_8);
        RzILOpEffect *for_11 = REPEAT(op_LT_4, seq_10);
        RzILOpEffect *seq_12 = SEQN(2, op_ASSIGN_2, for_11);
        RzILOpEffect *instruction_sequence = seq_12;

        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_reg_nums(self):
        self.assertEqual(Register.get_reg_num_from_name("V31:30"), 30)
        self.assertEqual(Register.get_reg_num_from_name("P0"), 0)
        self.assertIsNone(Register.get_reg_num_from_name("Pd"))
        self.assertIsNone(Register.get_reg_num_from_name("Pdd"))

    def test_reg_classes(self):
        self.assertEqual(
            Register("Rd", None, None).get_reg_class(), "HEX_REG_CLASS_INT_REGS"
        )
        self.assertEqual(
            Register("Rdd", None, None).get_reg_class(), "HEX_REG_CLASS_DOUBLE_REGS"
        )
        self.assertEqual(
            Register("Vdd", None, None).get_reg_class(), "HEX_REG_CLASS_HVX_WR"
        )
        self.assertEqual(
            Register("Vd", None, None).get_reg_class(), "HEX_REG_CLASS_HVX_VR"
        )
        self.assertEqual(
            Register("Qd", None, None).get_reg_class(), "HEX_REG_CLASS_HVX_QR"
        )
        self.assertEqual(
            Register("Cd", None, None).get_reg_class(), "HEX_REG_CLASS_CTR_REGS"
        )
        self.assertEqual(
            Register("Cdd", None, None).get_reg_class(), "HEX_REG_CLASS_CTR_REGS64"
        )
        self.assertIsNone(Register("lr", None, None, is_reg_alias=True).get_reg_class())

    def test_reg_alias_pc(self):
        behavior = "{ RdV = HEX_REG_ALIAS_PC; }"
        output = self.compile_behavior(behavior, self.get_new_transformer())
        expected = """
            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', false);
            RzILOpPure *pc = U32(pkt->pkt_addr);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_3 = WRITE_REG(bundle, Rd_op, CAST(32, IL_FALSE, pc));
            RzILOpEffect *instruction_sequence = op_ASSIGN_3;

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_n_reg(self):
        behavior = "{(siV); EA = RsV + siV; mem_store_u32(EA, (NtN)); }"
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            RzILOpPure *s = SN(32, (st32) ISA2IMM(hi, 's'));
            // Declare: ut32 EA;
            const HexOp *Rs_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);
            const HexOp Nt_new_op = NREG2OP(bundle, 't');
            RzILOpPure *Nt_new = READ_REG(pkt, &Nt_new_op, true);

            // EXEC
            RzILOpPure *op_ADD_4 = ADD(Rs, VARL("s"));

            // WRITE
            RzILOpEffect *imm_assign_0 = SETL("s", s);
            RzILOpEffect *op_ASSIGN_6 = SETL("EA", CAST(32, IL_FALSE, op_ADD_4));
            RzILOpEffect *ms_cast_ut32_8_9 = STOREW(VARL("EA"), CAST(32, IL_FALSE, Nt_new));
            RzILOpEffect *instruction_sequence = SEQN(3, imm_assign_0, op_ASSIGN_6, ms_cast_ut32_8_9);

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_trap(self):
        behavior = "{ trap(0, 0); }"
        self.assertEqual(
            self.compiler.sub_routines["trap"].body,
            """{\nreturn NOP();\n}""".replace("  ", ""),
        )
        ast = self.compiler.parser.parse(behavior)
        transformer = RZILTransformer(
            ArchEnum.HEXAGON, code_format=CodeFormat.EXEC_CLASSES
        )
        transformer.parameters = self.compiler.transformer.parameters
        transformer.sub_routines = self.compiler.transformer.sub_routines
        transformer.macros = self.compiler.transformer.macros
        output = transformer.transform(ast)
        expected = """
            // READ

            // EXEC

            // WRITE
            RzILOpEffect *trap_call_3 = hex_trap(SN(32, 0), CAST(32, IL_FALSE, SN(32, 0)));
            RzILOpEffect *instruction_sequence = trap_call_3;

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_reg_alias(self):
        behavior = "{ RdV = HEX_REG_ALIAS_USR; }"
        output = self.compile_behavior(behavior, self.get_new_transformer())
        expected = """
            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', false);
            const HexOp usr_op = ALIAS2OP(HEX_REG_ALIAS_USR, false);
            RzILOpPure *usr = READ_REG(pkt, &usr_op, false);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_3 = WRITE_REG(bundle, Rd_op, CAST(32, IL_FALSE, usr));
            RzILOpEffect *instruction_sequence = op_ASSIGN_3;

            return instruction_sequence;""".replace(
            "    ", ""
        )
        self.assertEqual(expected, output)

    def test_sign_change_on_reg_write(self):
        behavior = "{ RdV = (size1u_t)(mem_load_u8(EA)); uint32_t a = RdV; }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ
        const HexOp *Rd_op = ISA2REG(hi, 'd', false);
        // Declare: ut32 EA;
        // Declare: ut32 a;

        // EXEC
        RzILOpPure *ml_EA_2 = LOADW(8, VARL("EA"));

        // WRITE
        RzILOpEffect *op_ASSIGN_5 = WRITE_REG(bundle, Rd_op, CAST(32, IL_FALSE, CAST(8, IL_FALSE, ml_EA_2)));
        RzILOpEffect *op_ASSIGN_7 = SETL("a", CAST(32, IL_FALSE, READ_REG(pkt, Rd_op, true)));
        RzILOpEffect *instruction_sequence = SEQN(2, op_ASSIGN_5, op_ASSIGN_7);

        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_reg_jump_flag_setter(self):
        behavior = "{ JUMP(0x0); }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ

        // EXEC

        // WRITE
        RzILOpEffect *jump_const_0x0_0_1 = SEQ2(SETL("jump_flag", IL_TRUE), JMP(SN(32, 0)));
        RzILOpEffect *instruction_sequence = SEQN(2, jump_const_0x0_0_1, EMPTY());

        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_assign_op(self):
        behavior = "{ int32_t a = 1; a <<= 8; }"
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            // Declare: st32 a;

            // EXEC
            RzILOpPure *op_SHIFTL_4 = SHIFTL0(VARL("a"), SN(32, 8));

            // WRITE
            RzILOpEffect *op_ASSIGN_2 = SETL("a", SN(32, 1));
            RzILOpEffect *op_ASSIGN_LEFT_5 = SETL("a", op_SHIFTL_4);
            RzILOpEffect *instruction_sequence = SEQN(2, op_ASSIGN_2, op_ASSIGN_LEFT_5);

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_cast_bool(self):
        behavior = "{ uint32_t a; uint32_t b = ((uint32_t)(a == 1)); }"
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            // Declare: ut32 a;
            // Declare: ut32 b;

            // EXEC
            RzILOpPure *op_EQ_3 = EQ(VARL("a"), CAST(32, IL_FALSE, SN(32, 1)));
            RzILOpPure *ite_cast_ut32_4 = ITE(op_EQ_3, UN(32, 1), UN(32, 0));

            // WRITE
            RzILOpEffect *op_ASSIGN_6 = SETL("b", ite_cast_ut32_4);
            RzILOpEffect *instruction_sequence = op_ASSIGN_6;

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_unsigned_int(self):
        behavior = "{ unsigned int a; }"
        output = self.compile_behavior(behavior)
        expected = """
            // READ
            // Declare: ut32 a;

            // EXEC

            // WRITE
            RzILOpEffect *instruction_sequence = EMPTY();

            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_float_double_enc_dec(self):
        behavior = (
            "{"
            "int32_t RdV = fUNFLOAT(fFLOAT(RsV) + fFLOAT(RtV));"
            "int64_t RdV = fUNDOUBLE(fDOUBLE(RssV) - fDOUBLE(RttV));"
            "}"
        )
        self.compiler.transformer.code_format = CodeFormat.READ_STATEMENTS
        ast = self.compiler.parser.parse(behavior)
        output = self.compiler.transformer.transform(ast)
        self.compiler.transformer.code_format = CodeFormat.EXEC_CLASSES
        expected = """
            // READ
            const HexOp *Rs_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);
            const HexOp *Rt_op = ISA2REG(hi, 't', false);
            RzILOpPure *Rt = READ_REG(pkt, Rt_op, false);
            // Declare: st64 RdV;
            const HexOp *Rss_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rss = READ_REG(pkt, Rss_op, false);
            const HexOp *Rtt_op = ISA2REG(hi, 't', false);
            RzILOpPure *Rtt = READ_REG(pkt, Rtt_op, false);

            // RdV = ((st32) fUNFLOAT(fFLOAT(RZ_FLOAT_IEEE754_BIN_32, Rs) + fFLOAT(RZ_FLOAT_IEEE754_BIN_32, Rt)));
            RzILOpPure *op_ADD_4 = FADD(RZ_FLOAT_IEEE754_BIN_32, BV2F(RZ_FLOAT_IEEE754_BIN_32, Rs), BV2F(RZ_FLOAT_IEEE754_BIN_32, Rt));
            RzILOpEffect *op_ASSIGN_7 = SETL("RdV", CAST(32, IL_FALSE, F2BV(op_ADD_4)));

            // RdV = ((st64) ((st32) fUNDOUBLE(fDOUBLE(RZ_FLOAT_IEEE754_BIN_64, Rss) - fDOUBLE(RZ_FLOAT_IEEE754_BIN_64, Rtt))));
            RzILOpPure *op_SUB_13 = FSUB(RZ_FLOAT_IEEE754_BIN_64, BV2F(RZ_FLOAT_IEEE754_BIN_64, Rss), BV2F(RZ_FLOAT_IEEE754_BIN_64, Rtt));
            RzILOpEffect *op_ASSIGN_16 = SETL("RdV", CAST(64, MSB(CAST(32, IL_FALSE, F2BV(op_SUB_13))), CAST(32, IL_FALSE, F2BV(DUP(op_SUB_13)))));

            RzILOpEffect *instruction_sequence = SEQN(2, op_ASSIGN_7, op_ASSIGN_16);
            return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_fusr_fields(self):
        behavior = (
            "{"
            "uint32_t a = REGFIELD(RF_WIDTH, HEX_REG_FIELD_OVR);"
            "uint32_t b = REGFIELD(RF_OFFSET, HEX_REG_FIELD_OVR);"
            "}"
        )
        ast = self.compiler.parser.parse(behavior)
        transformer = RZILTransformer(
            ArchEnum.HEXAGON, code_format=CodeFormat.READ_STATEMENTS
        )
        transformer.parameters = self.compiler.transformer.parameters
        transformer.sub_routines = self.compiler.transformer.sub_routines
        transformer.macros = self.compiler.transformer.macros
        output = transformer.transform(ast)
        expected = """
        // READ
        // Declare: ut32 a;
        // Declare: ut32 b;

        // a = REGFIELD(RF_WIDTH, HEX_REG_FIELD_OVR);
        RzILOpEffect *op_ASSIGN_2 = SETL("a", HEX_REGFIELD(RF_WIDTH, HEX_REG_FIELD_OVR));

        // b = REGFIELD(RF_OFFSET, HEX_REG_FIELD_OVR);
        RzILOpEffect *op_ASSIGN_5 = SETL("b", HEX_REGFIELD(RF_OFFSET, HEX_REG_FIELD_OVR));

        RzILOpEffect *instruction_sequence = SEQN(2, op_ASSIGN_2, op_ASSIGN_5);
        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)

    def test_const_assign(self):
        behavior = "{ const uint32_t a; a = 1; }"
        self.assertRaises((ValueError, VisitError), self.compile_behavior, behavior)

    def test_gcc_extensions_stmt_in_expr_order(self):
        behavior = (
            "{ int k = 9;"
            "   uint32_t a = (k == 0) ? 1 : ({"
            "   int32_t x = 3;"
            "   5; "
            "}); "
            "}"
        )
        output = self.compile_behavior(
            behavior, self.get_new_transformer(CodeFormat.READ_STATEMENTS)
        )
        expected = """
            // READ
            // Declare: st32 k;
            // Declare: st32 x;
            // Declare: ut32 a;

            // k = 0x9;
            RzILOpEffect *op_ASSIGN_2 = SETL("k", SN(32, 9));

            // x = 0x3;
            RzILOpEffect *op_ASSIGN_8 = SETL("x", SN(32, 3));

            // HYB(gcc_expr_if ((k == 0x0)) {{}} else {x = 0x3}, 0x5);
            RzILOpPure *op_EQ_4 = EQ(VARL("k"), SN(32, 0));
            RzILOpEffect *gcc_expr_10 = BRANCH(op_EQ_4, EMPTY(), op_ASSIGN_8);

            // h_tmp0 = HYB(gcc_expr_if ((k == 0x0)) {{}} else {x = 0x3}, 0x5);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_12 = SETL("h_tmp0", SN(32, 5));

            // seq(HYB(gcc_expr_if ((k == 0x0)) {{}} else {x = 0x3}, 0x5); h_tm ...;
            RzILOpEffect *seq_13 = SEQN(2, gcc_expr_10, op_ASSIGN_hybrid_tmp_12);

            // a = ((ut32) ((k == 0x0) ? 0x1 : h_tmp0));
            RzILOpPure *cond_14 = ITE(DUP(op_EQ_4), SN(32, 1), VARL("h_tmp0"));
            RzILOpEffect *op_ASSIGN_16 = SETL("a", CAST(32, IL_FALSE, cond_14));

            // seq(seq(HYB(gcc_expr_if ((k == 0x0)) {{}} else {x = 0x3}, 0x5);  ...;
            RzILOpEffect *seq_17 = SEQN(2, seq_13, op_ASSIGN_16);

            RzILOpEffect *instruction_sequence = SEQN(2, op_ASSIGN_2, seq_17);
            return instruction_sequence;""".replace(
            "    ", ""
        )
        self.assertEqual(expected, output)

    def test_gcc_extensions_stmt_in_expr_ignore(self):
        behavior = (
            "{ "
            "   uint32_t a = (0 == 0) ? 1 : ({"
            "   int32_t x = 3;"
            "   5; "
            "}); "
            "}"
        )
        output = self.compile_behavior(behavior, self.get_new_transformer())
        expected = """
        // READ
        // Declare: st32 x;
        // Declare: ut32 a;

        // EXEC

        // WRITE
        RzILOpEffect *op_ASSIGN_13 = SETL("a", CAST(32, IL_FALSE, SN(32, 1)));
        RzILOpEffect *instruction_sequence = op_ASSIGN_13;

        return instruction_sequence;""".replace(
            "  ", ""
        )
        self.assertEqual(expected, output)


class TestGrammar(unittest.TestCase):
    def test_early_compatibility(self):
        # Setup parser
        with open(Conf.get_path(InputFile.GRAMMAR, ArchEnum.HEXAGON)) as f:
            grammar = "".join(f.readlines())
        exc = None
        try:
            self.parser = Lark(grammar, start="fbody", parser="earley")
        except Exception as e:
            exc = e
        self.assertIsNone(exc)

    @unittest.skip("LALR test: Grammar not yet LALR compatible.")
    def test_lalr_compatibility(self):
        # Setup parser
        with open(Conf.get_path(InputFile.GRAMMAR, ArchEnum.HEXAGON)) as f:
            grammar = "".join(f.readlines())
        exc = None
        logger.setLevel(logging.DEBUG)
        try:
            self.parser = Lark(grammar, start="fbody", parser="lalr", debug=True)
        except Exception as e:
            exc = e
        self.assertIsNone(exc)

    def test_and_ambiguity(self):
        behavior = "{ 0x0 & 0xffffff; 0x0 && 0xffffff; }"
        with open(Conf.get_path(InputFile.GRAMMAR, ArchEnum.HEXAGON)) as f:
            grammar = "".join(f.readlines())
        self.parser = Lark(grammar, start="fbody", parser="earley")
        ast = self.parser.parse(behavior)
        result = RZILTransformer(
            ArchEnum.HEXAGON, code_format=CodeFormat.EXEC_CLASSES
        ).transform(ast)
        self.assertNotIn("&", result)

    def test_gcc_extensions(self):
        behavior = (
            "{ uint32_t a = (0 == 0) ? 1 : ({" "   int32_t x = 1;" "   5; " "}); " "}"
        )
        with open(Conf.get_path(InputFile.GRAMMAR, ArchEnum.HEXAGON)) as f:
            grammar = "".join(f.readlines())
        self.parser = Lark(grammar, start="fbody", parser="earley")
        ast = self.parser.parse(behavior)
        result = RZILTransformer(
            ArchEnum.HEXAGON, code_format=CodeFormat.EXEC_CLASSES
        ).transform(ast)
        self.assertNotIn("&", result)


if __name__ == "__main__":
    TestTransforming().main()
    TestTransformerMeta().main()
    TestGrammar().main()
    TestTransformerOutput().main()
    TestTransformedInstr().main()
    TestStmtEmitting().main()
