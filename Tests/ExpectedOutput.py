# SPDX-FileCopyrightText: 2023 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

ExpectedOutput = {
    "Y2_barrier": "return NOP();",
    "A2_abs": (
        "\n"
        "// READ\n"
        "const char *Rd_assoc_tmp = ISA2REG(hi, 'd', true);\n"
        "const char *Rs_assoc = ISA2REG(hi, 's', false);\n"
        "RzILOpPure *Rs = VARG(Rs_assoc);\n"
        "\n"
        "// EXEC\n"
        "RzILOpPure *cast_1 = CAST(32, IL_FALSE, Rs);\n"
        "RzILOpPure *op_LT_0 = ULT(cast_1, UN(32, 0));\n"
        "RzILOpPure *op_NEG_2 = NEG(DUP(Rs));\n"
        "RzILOpPure *cond_3 = ITE(op_LT_0, op_NEG_2, DUP(Rs));\n"
        "\n"
        "// WRITE\n"
        "RzILOpEffect *op_ASSIGN_4 = HEX_WRITE_GLOBAL(Rd_assoc_tmp, cond_3);\n"
        "RzILOpEffect *instruction_sequence = op_ASSIGN_4;\n"
        "\n"
        "return instruction_sequence;"
    ),
    "L4_return": (
        "\n"
        "// READ\n"
        "// Declare: ut8 tmp;\n"
        "// Declare: ut32 EA;\n"
        "const char *Rs_assoc = ISA2REG(hi, 's', false);\n"
        "RzILOpPure *Rs = VARG(Rs_assoc);\n"
        "const char *Rdd_assoc_tmp = ISA2REG(hi, 'd', true);\n"
        "const char *framekey_assoc = ALIAS2REG(HEX_REG_ALIAS_FRAMEKEY, false);\n"
        "RzILOpPure *framekey = VARG(framekey_assoc);\n"
        "const char *sp_assoc_tmp = ALIAS2REG(HEX_REG_ALIAS_SP, true);\n"
        "\n"
        "// EXEC\n"
        "RzILOpPure *cast_1 = CAST(32, IL_FALSE, Rs);\n"
        'RzILOpPure *ml_EA_3 = LOADW(64, VARL("EA"));\n'
        "RzILOpPure *cast_ut8_4 = CAST(8, IL_FALSE, ml_EA_3);\n"
        "RzILOpPure *cast_ut64_6 = CAST(64, IL_FALSE, framekey);\n"
        "RzILOpPure *op_LSHIFT_7 = SHIFTL0(cast_ut64_6, UN(32, 32));\n"
        'RzILOpPure *cast_9 = CAST(64, IL_FALSE, VARL("tmp"));\n'
        "RzILOpPure *op_XOR_8 = LOGXOR(cast_9, op_LSHIFT_7);\n"
        "RzILOpPure *cast_11 = CAST(64, MSB(DUP(op_XOR_8)), op_XOR_8);\n"
        'RzILOpPure *op_ADD_12 = ADD(VARL("EA"), UN(32, 8));\n'
        "RzILOpPure *op_MUL_14 = MUL(UN(32, 1), UN(32, 32));\n"
        "RzILOpPure *op_RSHIFT_15 = SHIFTR0(VARG(Rdd_assoc_tmp), op_MUL_14);\n"
        "RzILOpPure *op_AND_16 = LOGAND(op_RSHIFT_15, SN(64, 4294967295));\n"
        "RzILOpPure *cast_st64_18 = CAST(64, MSB(DUP(op_AND_16)), op_AND_16);\n"
        "\n"
        "// WRITE\n"
        'RzILOpEffect *op_ASSIGN_0 = SETL("EA", cast_1);\n'
        "RzILOpEffect *empty_2 = EMPTY();\n"
        'RzILOpEffect *op_ASSIGN_5 = SETL("tmp", cast_ut8_4);\n'
        "RzILOpEffect *op_ASSIGN_10 = HEX_WRITE_GLOBAL(Rdd_assoc_tmp, cast_11);\n"
        "RzILOpEffect *op_ASSIGN_13 = HEX_WRITE_GLOBAL(sp_assoc_tmp, op_ADD_12);\n"
        "RzILOpEffect *jump_cast_st64_18 = JMP(cast_st64_18);\n"
        "RzILOpEffect *empty_19 = EMPTY();\n"
        "RzILOpEffect *instruction_sequence = SEQN(7, op_ASSIGN_0, empty_2, op_ASSIGN_5, op_ASSIGN_10, op_ASSIGN_13, jump_cast_st64_18, empty_19);\n"
        "\n"
        "return instruction_sequence;"
    ),
    "J2_jump": (
        '\n'
        '// READ\n'
        "RzILOpPure *r = SN(32, (st32) ISA2IMM(hi, 'r'));\n"
        'RzILOpPure *pc = U32(pkt->pkt_addr);\n'
        '\n'
        '// EXEC\n'
        'RzILOpPure *op_NOT_1 = LOGNOT(UN(32, 3));\n'
        'RzILOpPure *cast_3 = CAST(32, IL_FALSE, VARL("r"));\n'
        'RzILOpPure *op_AND_2 = LOGAND(cast_3, op_NOT_1);\n'
        'RzILOpPure *cast_5 = CAST(32, MSB(DUP(op_AND_2)), op_AND_2);\n'
        'RzILOpPure *cast_7 = CAST(32, IL_FALSE, VARL("r"));\n'
        'RzILOpPure *op_ADD_6 = ADD(pc, cast_7);\n'
        '\n'
        '// WRITE\n'
        'RzILOpEffect *imm_assign_0 = SETL("r", r);\n'
        'RzILOpEffect *op_ASSIGN_4 = SETL("r", cast_5);\n'
        'RzILOpEffect *jump_op_ADD_6 = JMP(op_ADD_6);\n'
        'RzILOpEffect *empty_8 = EMPTY();\n'
        'RzILOpEffect *instruction_sequence = SEQN(4, imm_assign_0, op_ASSIGN_4, jump_op_ADD_6, empty_8);\n'
        '\n'
        'return instruction_sequence;'
    ),
}
