# SPDX-FileCopyrightText: 2023 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

ExpectedOutput = {
    "Y2_barrier": "return NOP();",
    "A2_abs": ("\n"
               "// READ\n"
               "const char *Rd_assoc_tmp = ISA2REG(hi, 'd', true);\n"
               "const char *Rs_assoc = ISA2REG(hi, 's', false);\n"
               "RzILOpPure *Rs = VARG(Rs_assoc);\n"
               "RzILOpPure *const_pos0 = UN(32, 0x0);\n"
               "\n"
               "// EXEC\n"
               "RzILOpPure *cast_1 = CAST(32, IL_FALSE, Rs);\n"
               'RzILOpPure *op_LT_0 = LET("const_pos0", const_pos0, ULT(cast_1, VARLP("const_pos0")));\n'
               "RzILOpPure *op_NEG_2 = NEG(DUP(Rs));\n"
               "RzILOpPure *cond_3 = ITE(op_LT_0, op_NEG_2, DUP(Rs));\n"
               "\n"
               "// WRITE\n"
               "RzILOpEffect *op_ASSIGN_4 = HEX_WRITE_GLOBAL(Rd_assoc_tmp, cond_3);\n"
               "RzILOpEffect *instruction_sequence = SEQN(1, op_ASSIGN_4);\n"
               "\n"
               "return instruction_sequence;")
}
