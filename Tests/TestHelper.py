#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import unittest

from rzil_compiler.Transformer.Pures.Pure import ValueType
from rzil_compiler.Transformer.helper import get_value_type_by_c_type


class TestHelper(unittest.TestCase):
    def test_c_type_to_value_type(self):
        uint64_t = get_value_type_by_c_type("uint64_t")
        self.assertEqual(uint64_t, ValueType(False, 64))
        int8_t = get_value_type_by_c_type("int8_t")
        self.assertEqual(int8_t, ValueType(True, 8))
        int_t = get_value_type_by_c_type("int")
        self.assertEqual(int_t, ValueType(True, 32))
        unsigned = get_value_type_by_c_type("unsigned")
        self.assertEqual(unsigned, ValueType(False, 32))
        size7s_t = get_value_type_by_c_type("size7s_t")
        self.assertEqual(size7s_t, ValueType(True, 7))


if __name__ == "__main__":
    TestHelper().main()
