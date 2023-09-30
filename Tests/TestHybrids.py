#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import unittest

from rzil_compiler.Transformer.Hybrids.SubRoutine import SubRoutine, SubRoutineInitType
from rzil_compiler.Transformer.Pures.Parameter import Parameter
from rzil_compiler.Transformer.ValueType import (
    ValueType,
    get_value_type_by_c_type,
    split_var_decl,
)
from rzil_compiler.Transformer.RZILTransformer import RZILTransformer
from rzil_compiler.ArchEnum import ArchEnum
from rzil_compiler.Compiler import Compiler


class TestHybrids(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = 1000
        cls.compiler = Compiler(ArchEnum.HEXAGON)

    def test_sub_routines(self):
        self.assertEqual(self.compiler.sub_routines["sextract64"].value_type, ValueType(True, 64))
        self.assertEqual(self.compiler.sub_routines["sextract64"].routine_name, "sextract64")
        self.assertEqual(
            self.compiler.sub_routines["sextract64"].il_init(SubRoutineInitType.DECL),
            "RZ_OWN RzILOpEffect *hex_sextract64("
            "RZ_BORROW RzILOpPure *value, "
            "RZ_BORROW RzILOpPure *start, "
            "RZ_BORROW RzILOpPure *length)",
        )
        self.assertTrue(
            'RzILOpEffect *set_return_val_12 = SETL("ret_val", op_RSHIFT_10);'
            in self.compiler.sub_routines["sextract64"].il_init(SubRoutineInitType.DEF)
        )

    def test_sub_routine_2(self):
        ret_val = "uint64_t"
        params = ["uint64_t value", "int start", "int length"]
        behavior = "{ return (value >> start) & (~0ULL >> (64 - length)); }"
        exc = None
        try:
            self.compiler.compile_sub_routine("dummy", ret_val, params, behavior)
        except Exception as e:
            exc = e
        self.assertIsNone(exc)

    def test_set_c9_jump_call(self):
        code = "{ JUMP(0x0); }"
        # Compile the body
        ast_body = self.compiler.parser.parse(code)
        result = RZILTransformer(
            ArchEnum.HEXAGON,
            parameters=[Parameter("bundle", get_value_type_by_c_type("HexPktInsnBundle *"))],
            return_type=self.compiler.sub_routines["set_c9_jump"].value_type,
            sub_routines=self.compiler.sub_routines
        ).transform(ast_body)
        self.assertEqual("""
        // READ
        const HexOp c9_new_op = EXPLICIT2OP(9, HEX_REG_CLASS_CTR_REGS, true);

        // EXEC

        // WRITE
        RzILOpEffect *set_c9_jump_call_2 = hex_set_c9_jump(bundle, &c9_new_op, UN(32, 0));
        RzILOpEffect *instruction_sequence = SEQN(2, set_c9_jump_call_2, EMPTY());

        return instruction_sequence;""".replace("  ", ""), result)

    def test_set_c9_jump_def(self):
        self.assertEqual("""RZ_OWN RzILOpEffect *hex_set_c9_jump(HexInsnPktBundle *bundle, const HexOp *C9_op, RZ_BORROW RzILOpPure *target_addr) {
        HexPkt *pkt = bundle->pkt;

        // READ

        // EXEC

        // WRITE
        RzILOpEffect *c_call_0 = WRITE_REG(pkt, C9_op, target_addr);
        RzILOpEffect *jump_target_addr_1 = JMP(DUP(target_addr));
        RzILOpEffect *instruction_sequence = SEQN(3, c_call_0, jump_target_addr_1, EMPTY());

        return instruction_sequence;
        }""".replace("  ", ""),
                         self.compiler.sub_routines["set_c9_jump"].il_init(SubRoutineInitType.DEF)
                         )


if __name__ == "__main__":
    TestHybrids().main()
