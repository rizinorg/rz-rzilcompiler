#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import logging
import re
import unittest

from Compiler import RZILInstruction, Compiler
from rzil_compiler.Transformer.Hybrids.SubRoutine import SubRoutine, SubRoutineInitType
from rzil_compiler.Transformer.Pures.Parameter import get_parameter_by_decl, Parameter
from rzil_compiler.Transformer.ValueType import get_value_type_by_c_type, ValueType, VTGroup
from rzil_compiler.Transformer.Pures.Register import Register
from rzil_compiler.Transformer.Pures.Cast import Cast
from rzil_compiler.Transformer.Pures.Number import Number
from rzil_compiler.Configuration import Conf, InputFile
from rzil_compiler.Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
from rzil_compiler.Transformer.RZILTransformer import RZILTransformer
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
        cls.insn_behavior = get_hexagon_insn_behavior()
        cls.parser = get_hexagon_parser()
        cls.compiler = Compiler(ArchEnum.HEXAGON)

    def compile_behavior(
        self, behavior: str, transformer: RZILTransformer = None
    ) -> Exception:
        exception = None
        try:
            tree = self.parser.parse(behavior)
            if transformer:
                transformer.transform(tree)
            else:
                transformer = RZILTransformer(ArchEnum.HEXAGON, sub_routines=self.compiler.sub_routines,
                        parameters=[Parameter("pkt", get_value_type_by_c_type("HexPkt")),
                                    Parameter("hi", get_value_type_by_c_type("HexInsn")),
                                    Parameter("bundle", get_value_type_by_c_type("HexInsnPktBundle"))
                                    ],
                        return_type=ValueType(False, 32, VTGroup.EXTERNAL, "RzILOpEffect"),
                        )
                transformer.transform(tree)
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
            ArchEnum.HEXAGON, parameters=params, return_type=ret_val
        )
        exc = self.compile_behavior(behavior, transformer)
        self.assertIsNone(exc)

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
        cls.compiler = Compiler(ArchEnum.HEXAGON)

    def compile_behavior(self, behavior: str) -> list[str]:
        try:
            tree = self.parser.parse(behavior)
            transformer = RZILTransformer(ArchEnum.HEXAGON, sub_routines=self.compiler.sub_routines,
                        parameters=[
                            Parameter("pkt", get_value_type_by_c_type("HexPkt")),
                            Parameter("hi", get_value_type_by_c_type("HexInsn")),
                            Parameter("bundle", get_value_type_by_c_type("HexInsnPktBundle"))
                        ],
                        return_type=ValueType(False, 32, VTGroup.EXTERNAL, "RzILOpEffect"),
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
        cls.compiler = Compiler(ArchEnum.HEXAGON)
        cls.transformer = RZILTransformer(ArchEnum.HEXAGON)

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
            ArchEnum.HEXAGON, parameters=params, return_type=ret_type
        ).transform(ast_body)
        sub_routine = SubRoutine(name, ret_type, params, body)

        self.assertEqual(
            """RZ_OWN RzILOpEffect *hex_test_routine(HexInsnPktBundle *bundle, const HexOp *RdV, RZ_BORROW RzILOpPure *start, const HexOp *RsV) {
            const HexInsn *hi = bundle->insn;
            HexPkt *pkt = bundle->pkt;

            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', true);
            const HexOp *Rs_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);

            // EXEC
            RzILOpPure *op_ADD_2 = ADD(Rs, start);

            // WRITE
            RzILOpEffect *op_ASSIGN_3 = WRITE_REG(pkt, Rd_op, op_ADD_2);
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
        ).transform(ast_body)

        self.assertEqual(
            """
            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', true);
            const HexOp *Rs_op = ISA2REG(hi, 's', false);
            RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);

            // EXEC

            // WRITE
            RzILOpEffect *test_routine_call_4 = hex_test_routine(bundle, Rd_op, CAST(32, MSB(UN(32, 0)), UN(32, 0)), Rs_op);
            RzILOpEffect *op_ASSIGN_hybrid_tmp_5 = SETL("h_tmp0", UNSIGNED(64, VARL("ret_val")));
            RzILOpEffect *seq_6 = SEQN(2, test_routine_call_4, op_ASSIGN_hybrid_tmp_5);
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
            ArchEnum.HEXAGON, sub_routines={"sextract64": sub_routine}
        )
        result = transformer.transform(ast_body)
        self.assertEqual(
            """
            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', true);

            // EXEC

            // WRITE
            RzILOpEffect *sextract64_call_7 = hex_sextract64(CAST(64, IL_FALSE, UN(32, 0)), CAST(32, MSB(UN(32, 0)), UN(32, 0)), CAST(32, MSB(UN(32, 0)), UN(32, 0)));
            RzILOpEffect *op_ASSIGN_hybrid_tmp_8 = SETL("h_tmp0", SIGNED(64, VARL("ret_val")));
            RzILOpEffect *seq_9 = SEQN(2, sextract64_call_7, op_ASSIGN_hybrid_tmp_8);
            RzILOpEffect *op_ASSIGN_11 = WRITE_REG(pkt, Rd_op, CAST(32, MSB(VARL("h_tmp0")), VARL("h_tmp0")));
            RzILOpEffect *seq_12 = SEQN(2, seq_9, op_ASSIGN_11);
            RzILOpEffect *instruction_sequence = seq_12;

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
            ArchEnum.HEXAGON, parameters=params, return_type=ret_val
        )
        output = self.compile_behavior(behavior, transformer)
        self.assertEqual(
            """
            // READ

            // EXEC
            RzILOpPure *op_RSHIFT_0 = SHIFTR0(value, start);
            RzILOpPure *op_SUB_5 = SUB(UN(32, 0x40), CAST(32, IL_FALSE, length));
            RzILOpPure *op_RSHIFT_6 = SHIFTR0(UN(64, -1), op_SUB_5);
            RzILOpPure *op_AND_7 = LOGAND(op_RSHIFT_0, op_RSHIFT_6);

            // WRITE
            RzILOpEffect *set_return_val_9 = SETL("ret_val", op_AND_7);
            RzILOpEffect *instruction_sequence = set_return_val_9;

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
            "RzILOpPure *const_pos0_0 = UN(32, 0x0);\n"
            "// Declare: ut64 a;\n\n"
            "// EXEC\n"
            'RzILOpPure *cast_ut8_1 = LET("const_pos0_0", const_pos0_0, CAST(8, IL_FALSE, VARLP("const_pos0_0")));\n'
            "RzILOpPure *cast_ut64_3 = CAST(64, IL_FALSE, cast_ut8_1);"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_cast_simplification_2(self):
        behavior = "{ uint64_t a = ((int64_t)((int8_t)((int32_t) 0))); }"
        self.transformer.inlined_pure_classes = ()
        output = self.compile_behavior(behavior)
        expected = (
            "RzILOpPure *const_pos0_0 = UN(32, 0x0);\n"
            "// Declare: ut64 a;\n\n"
            "// EXEC\n"
            'RzILOpPure *cast_st8_2 = LET("const_pos0_0", const_pos0_0, CAST(8, MSB(VARLP("const_pos0_0")), VARLP("const_pos0_0")));\n'
            "RzILOpPure *cast_st64_3 = CAST(64, MSB(cast_st8_2), DUP(cast_st8_2));\n"
            "RzILOpPure *cast_ut64_6 = CAST(64, IL_FALSE, cast_st64_3);"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_simplify_arith_expr(self):
        # Simplify e.g. 4 - 1 = 3
        behavior = "{ uint32_t a = 1 + 1 * 7; }"
        output = self.compile_behavior(behavior)
        expected = "// WRITE\n" 'RzILOpEffect *op_ASSIGN_6 = SETL("a", UN(32, 8));\n'
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
        RzILOpEffect *op_ASSIGN_3 = SETL("a", UN(32, -4));
        RzILOpEffect *instruction_sequence = op_ASSIGN_3;
        
        return instruction_sequence;""".replace("  ", "")
        self.assertEqual(
            expected, output)

    def test_simplify_unary_expr_pm(self):
        behavior = "{ uint32_t a = +8 + - +5;  }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ
        // Declare: ut32 a;

        // EXEC

        // WRITE
        RzILOpEffect *op_ASSIGN_5 = SETL("a", UN(32, 3));
        RzILOpEffect *instruction_sequence = op_ASSIGN_5;

        return instruction_sequence;""".replace("  ", "")
        self.assertEqual(
            expected, output)

    def test_simplify_unary_expr_minus(self):
        behavior = "{ int32_t a = -(+0x3);  }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ
        // Declare: st32 a;

        // EXEC

        // WRITE
        RzILOpEffect *op_ASSIGN_3 = SETL("a", SN(32, -3));
        RzILOpEffect *instruction_sequence = op_ASSIGN_3;

        return instruction_sequence;""".replace("  ", "")
        self.assertEqual(
            expected, output)

    def test_simplify_unary_expr_minus(self):
        behavior = "{ uint32_t a = +10 - -2;  }"
        output = self.compile_behavior(behavior)
        expected = """
        // READ
        // Declare: ut32 a;

        // EXEC

        // WRITE
        RzILOpEffect *op_ASSIGN_4 = SETL("a", UN(32, 12));
        RzILOpEffect *instruction_sequence = op_ASSIGN_4;

        return instruction_sequence;""".replace("  ", "")
        self.assertEqual(
            expected, output)

    def test_inlining_nothing(self):
        behavior = "{ int64_t a = 0; }"
        self.transformer.inlined_pure_classes = ()
        output = self.compile_behavior(behavior)
        expected = (
            "\n"
            "// READ\n"
            "RzILOpPure *const_pos0_0 = UN(32, 0x0);\n"
            "// Declare: st64 a;\n\n"
            "// EXEC\n"
            'RzILOpPure *cast_st64_3 = LET("const_pos0_0", const_pos0_0, CAST(64, MSB(VARLP("const_pos0_0")), VARLP("const_pos0_0")));\n\n'
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
            "RzILOpPure *cast_st64_3 = CAST(64, MSB(UN(32, 0)), UN(32, 0));\n\n"
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
            "RzILOpPure *const_pos0_0 = UN(32, 0x0);\n"
            "// Declare: st64 a;\n\n"
            "// EXEC\n\n"
            "// WRITE\n"
            'RzILOpEffect *op_ASSIGN_2 = SETL("a", LET("const_pos0_0", const_pos0_0, CAST(64, MSB(VARLP("const_pos0_0")), VARLP("const_pos0_0"))));\n'
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
            'RzILOpEffect *op_ASSIGN_2 = SETL("a", CAST(64, MSB(UN(32, 0)), UN(32, 0)));\n'
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_store_cancelled_fcn(self):
        behavior = "{ STORE_SLOT_CANCELLED(slot); }"
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
            "const HexOp *Rd_op = ISA2REG(hi, 'd', true);\n\n"
            "// EXEC\n\n// WRITE\n"
            "RzILOpEffect *op_ASSIGN_3 = WRITE_REG(pkt, Rd_op, CAST(32, MSB(UN(32, 0)), UN(32, 0)));\n"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_reg_read(self):
        behavior = "{ RdV = RsV; }"
        output = self.compile_behavior(behavior)
        expected = (
            "// READ\n"
            "const HexOp *Rd_op = ISA2REG(hi, 'd', true);\n"
            "const HexOp *Rs_op = ISA2REG(hi, 's', false);\n"
            "RzILOpPure *Rs = READ_REG(pkt, Rs_op, false);\n\n"
            "// EXEC\n\n// WRITE\n"
            "RzILOpEffect *op_ASSIGN_2 = WRITE_REG(pkt, Rd_op, Rs);\n"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_reg_read_write(self):
        behavior = "{ RxV = RxV; }"
        output = self.compile_behavior(behavior)
        expected = (
            "// READ\n"
            "const HexOp *Rx_op = ISA2REG(hi, 'x', true);\n"
            "RzILOpPure *Rx = READ_REG(pkt, Rx_op, false);\n\n"
            "// EXEC\n\n// WRITE\n"
            "RzILOpEffect *op_ASSIGN_1 = WRITE_REG(pkt, Rx_op, Rx);\n"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )

    def test_reg_explicit_assign(self):
        behavior = "{ P1_NEW = P0; R11:10_NEW = C31:30; }"
        output = self.compile_behavior(behavior)
        expected = (
            """
            // READ
            const HexOp P1_new_op = EXPLICIT2OP(1, HEX_REG_CLASS_PRED_REGS, true);
            const HexOp P0_op = EXPLICIT2OP(0, HEX_REG_CLASS_PRED_REGS, false);
            RzILOpPure *P0 = READ_REG(pkt, &P0_op, false);
            const HexOp R11_10_new_op = EXPLICIT2OP(10, HEX_REG_CLASS_DOUBLE_REGS, true);
            const HexOp C31_30_op = EXPLICIT2OP(30, HEX_REG_CLASS_CTR_REGS64, false);
            RzILOpPure *C31_30 = READ_REG(pkt, &C31_30_op, false);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_2 = WRITE_REG(pkt, &P1_new_op, P0);
            RzILOpEffect *op_ASSIGN_5 = WRITE_REG(pkt, &R11_10_new_op, C31_30);
            RzILOpEffect *instruction_sequence = SEQN(2, op_ASSIGN_2, op_ASSIGN_5);

            return instruction_sequence;""".replace("  ", "")
        )
        self.assertEqual(
            expected, output
        )

    def test_reg_explicit_new(self):
        behavior = "{ P0 = P0_NEW; }"
        output = self.compile_behavior(behavior)
        expected = (
            """
            // READ
            const HexOp P0_op = EXPLICIT2OP(0, HEX_REG_CLASS_PRED_REGS, true);
            const HexOp P0_new_op = EXPLICIT2OP(0, HEX_REG_CLASS_PRED_REGS, true);
            RzILOpPure *P0_new = READ_REG(pkt, &P0_new_op, true);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_2 = WRITE_REG(pkt, &P0_op, P0_new);
            RzILOpEffect *instruction_sequence = op_ASSIGN_2;

            return instruction_sequence;""".replace("  ", "")
        )
        self.assertEqual(
            expected, output
        )

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
        output = self.compile_behavior(behavior)
        expected = (
            """
            // READ
            const HexOp *Rd_op = ISA2REG(hi, 'd', true);
            RzILOpPure *pc = U32(pkt->pkt_addr);

            // EXEC

            // WRITE
            RzILOpEffect *op_ASSIGN_3 = WRITE_REG(pkt, Rd_op, CAST(32, MSB(pc), DUP(pc)));
            RzILOpEffect *instruction_sequence = op_ASSIGN_3;

            return instruction_sequence;""".replace("  ", "")
        )
        self.assertEqual(
            expected, output
        )

    def test_reg_alias(self):
        behavior = "{ RdV = HEX_REG_ALIAS_USR; }"
        output = self.compile_behavior(behavior)
        expected = (
            "// READ\n"
            "const HexOp *Rd_op = ISA2REG(hi, 'd', true);\n"
            "const HexOp usr_op = ALIAS2OP(HEX_REG_ALIAS_USR, false);\n"
            "RzILOpPure *usr = READ_REG(pkt, &usr_op, false);\n\n"
            "// EXEC\n\n// WRITE\n"
            "RzILOpEffect *op_ASSIGN_3 = WRITE_REG(pkt, Rd_op, CAST(32, MSB(usr), DUP(usr)));\n"
        )
        self.assertTrue(
            expected in output, msg=f"\nEXPECTED:\n{expected}\nin\nOUTPUT:\n{output}"
        )


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
        result = RZILTransformer(ArchEnum.HEXAGON).transform(ast)
        self.assertNotIn("&", result)


if __name__ == "__main__":
    TestTransforming().main()
    TestTransformerMeta().main()
    TestGrammar().main()
    TestTransformerOutput().main()
    TestTransformedInstr().main()
