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
        'RzILOpPure *op_LT_3 = ULT(CAST(32, IL_FALSE, Rs), UN(32, 0));\n'
        'RzILOpPure *op_NEG_4 = NEG(DUP(Rs));\n'
        'RzILOpPure *cond_5 = ITE(op_LT_3, op_NEG_4, DUP(Rs));\n'
        '\n'
        '// WRITE\n'
        'RzILOpEffect *op_ASSIGN_6 = HEX_WRITE_GLOBAL(Rd_assoc_tmp, cond_5);\n'
        'RzILOpEffect *instruction_sequence = op_ASSIGN_6;\n'
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
        "const char *framekey_assoc = ALIAS2REG(HEX_REG_ALIAS_FRAMEKEY_7, false);\n"
        "RzILOpPure *framekey = VARG(framekey_assoc);\n"
        "const char *sp_assoc_tmp = ALIAS2REG(HEX_REG_ALIAS_SP_13, true);\n"
        "\n"
        "// EXEC\n"
        'RzILOpPure *ml_EA_3 = LOADW(64, VARL("EA"));\n'
        "RzILOpPure *op_LSHIFT_10 = SHIFTL0(CAST(64, IL_FALSE, framekey), UN(32, 32));\n"
        'RzILOpPure *op_XOR_11 = LOGXOR(CAST(64, IL_FALSE, VARL("tmp")), op_LSHIFT_10);\n'
        'RzILOpPure *op_ADD_15 = ADD(VARL("EA"), UN(32, 8));\n'
        "RzILOpPure *op_RSHIFT_20 = SHIFTR0(VARG(Rdd_assoc_tmp), UN(32, 32));\n"
        "RzILOpPure *op_AND_22 = LOGAND(op_RSHIFT_20, SN(64, 4294967295));\n"
        "\n"
        "// WRITE\n"
        'RzILOpEffect *op_ASSIGN_1 = SETL("EA", CAST(32, IL_FALSE, Rs));\n'
        "\n"
        'RzILOpEffect *op_ASSIGN_5 = SETL("tmp", CAST(8, IL_FALSE, ml_EA_3));\n'
        "RzILOpEffect *op_ASSIGN_12 = HEX_WRITE_GLOBAL(Rdd_assoc_tmp, CAST(64, MSB(DUP(op_XOR_11)), op_XOR_11));\n"
        "RzILOpEffect *op_ASSIGN_16 = HEX_WRITE_GLOBAL(sp_assoc_tmp, op_ADD_15);\n"
        "RzILOpEffect *jump_cast_st64_24_25 = JMP(CAST(64, MSB(DUP(op_AND_22)), op_AND_22));\n"
        "\n"
        "RzILOpEffect *instruction_sequence = SEQN(7, op_ASSIGN_1, EMPTY(), op_ASSIGN_5, op_ASSIGN_12, op_ASSIGN_16, jump_cast_st64_24_25, EMPTY());\n"
        "\n"
        "return instruction_sequence;"
    ),
    "J2_jump": (
        "\n"
        "// READ\n"
        "RzILOpPure *r = SN(32, (st32) ISA2IMM(hi, 'r'));\n"
        "RzILOpPure *pc = U32(pkt->pkt_addr);\n"
        "\n"
        "// EXEC\n"
        "RzILOpPure *op_NOT_5 = LOGNOT(UN(32, 3));\n"
        'RzILOpPure *op_AND_6 = LOGAND(CAST(32, IL_FALSE, VARL("r")), op_NOT_5);\n'
        'RzILOpPure *op_ADD_9 = ADD(pc, CAST(32, IL_FALSE, VARL("r")));\n'
        "\n"
        "// WRITE\n"
        'RzILOpEffect *imm_assign_0 = SETL("r", r);\n'
        'RzILOpEffect *op_ASSIGN_7 = SETL("r", CAST(32, MSB(DUP(op_AND_6)), op_AND_6));\n'
        "RzILOpEffect *jump_op_ADD_9_10 = JMP(op_ADD_9);\n"
        "\n"
        "RzILOpEffect *instruction_sequence = SEQN(4, imm_assign_0, op_ASSIGN_7, jump_op_ADD_9_10, EMPTY());\n"
        "\n"
        "return instruction_sequence;"
    ),
}
