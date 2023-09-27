#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import unittest

from rzil_compiler.Transformer.Hybrids.SubRoutine import SubRoutine, SubRoutineInitType
from rzil_compiler.Transformer.Pures.Parameter import Parameter
from rzil_compiler.Transformer.ValueType import ValueType, get_value_type_by_c_type
from rzil_compiler.Transformer.RZILTransformer import RZILTransformer
from rzil_compiler.ArchEnum import ArchEnum
from rzil_compiler.Compiler import Compiler


class TestHybrids(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = Compiler(ArchEnum.HEXAGON)

    def test_sub_routines(self):
        name = "sextract64"
        return_type = "int64_t"
        parameters = ["uint64_t value", "int start", "int length"]
        code = (
            "{ return ((int32_t)(value << (32 - length - start))) >> (32 - length); }"
        )
        params = list()
        for param in parameters:
            ptype, pname = param.split(" ")
            params.append(Parameter(pname, get_value_type_by_c_type(ptype)))

        ret_type = get_value_type_by_c_type(return_type)
        # Compile the body
        ast_body = self.compiler.parser.parse(code)
        transformed_body = RZILTransformer(
            ArchEnum.HEXAGON, parameters=params, return_type=ret_type
        ).transform(ast_body)
        sub_routine = SubRoutine(name, ret_type, params, transformed_body)
        self.assertEqual(sub_routine.value_type, ValueType(True, 64))
        self.assertEqual(sub_routine.routine_name, "sextract64")
        self.assertEqual(
            sub_routine.il_init(SubRoutineInitType.DECL),
            "RZ_OWN RzILOpEffect *hex_sextract64("
            "RZ_BORROW RzILOpPure *value, "
            "RZ_BORROW RzILOpPure *start, "
            "RZ_BORROW RzILOpPure *length)",
        )
        self.assertTrue(
            'RzILOpEffect *set_return_val_12 = SETL("ret_val", op_RSHIFT_10);'
            in sub_routine.il_init(SubRoutineInitType.DEF)
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


if __name__ == "__main__":
    TestHybrids().main()
