// SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
// SPDX-License-Identifier: LGPL-3.0-only

// Macros in this file fill replace the qualcomm macros from the Qemu source.

#define DEF_SHORTCODE(TAG, SHORTCODE) insn(TAG, SHORTCODE)

#define RF_WIDTH HEX_RF_WIDTH
#define RF_OFFSET HEX_RF_OFFSET

#define MEM_LOAD1s(VA) (mem_load_s8(VA))
#define MEM_LOAD1u(VA) (mem_load_u8(VA))
#define MEM_LOAD2s(VA) (mem_load_s16(VA))
#define MEM_LOAD2u(VA) (mem_load_u16(VA))
#define MEM_LOAD4s(VA) (mem_load_s32(VA))
#define MEM_LOAD4u(VA) (mem_load_u32(VA))
#define MEM_LOAD8s(VA) (mem_load_s64(VA))
#define MEM_LOAD8u(VA) (mem_load_u64(VA))

#define MEM_STORE1(VA, DATA, SLOT) mem_store_u8(VA, DATA)
#define MEM_STORE2(VA, DATA, SLOT) mem_store_u16(VA, DATA)
#define MEM_STORE4(VA, DATA, SLOT) mem_store_u32(VA, DATA)
#define MEM_STORE8(VA, DATA, SLOT) mem_store_u64(VA, DATA)

#define CANCEL cancel_slot

#define fPART1(WORK) __COMPOUND_PART1__{ WORK; }__COMPOUND_PART1__

#define fIMMEXT(IMM) (IMM)

#define fWRITE_NPC(A) JUMP(A)

#define READ_REG(NUM)                    NUM
#define READ_PREG(NUM)                   P##NUM
#define WRITE_RREG(NUM, VAL)             (NUM = VAL);
#define WRITE_PREG(NUM, VAL)             READ_PREG(NUM) = VAL

#define fREAD_GP() \
    (insn->extension_valid ? 0 : READ_REG(HEX_REG_GP))

#define fREAD_P0 READ_PREG(0)

#define fREAD_LR() (READ_REG(HEX_REG_LR))
#define fREAD_SP() (READ_REG(HEX_REG_SP))
#define fREAD_LC0 (READ_REG(HEX_REG_LC0))
#define fREAD_LC1 (READ_REG(HEX_REG_LC1))
#define fREAD_SA0 (READ_REG(HEX_REG_SA0))
#define fREAD_SA1 (READ_REG(HEX_REG_SA1))
#define fREAD_FP() (READ_REG(HEX_REG_FP))
#define fGET_FRAMEKEY() (READ_REG(HEX_REG_FRAMEKEY))

#define PC HEX_REG_ALIAS_PC

#define fWRITE_LR(A) (HEX_REG_ALIAS_LR = A)
#define fWRITE_FP(A) (HEX_REG_ALIAS_FP = A)
#define fWRITE_SP(A) (HEX_REG_ALIAS_SP = A)
#define fWRITE_LOOP_REGS0(START, COUNT) HEX_REG_ALIAS_SA0 = START; (HEX_REG_ALIAS_LC0 = COUNT)
#define fWRITE_LOOP_REGS1(START, COUNT) HEX_REG_ALIAS_SA1 = START; (HEX_REG_ALIAS_LC1 = COUNT)
#define fWRITE_LC1(VAL) (HEX_REG_ALIAS_LC1 = VAL)
#define fSET_LPCFG(VAL) SET_USR_FIELD(LPCFG, VAL)

#define HEX_REG_LR   HEX_REG_ALIAS_LR
#define HEX_REG_R31   R31
#define HEX_REG_SA0   HEX_REG_ALIAS_SA0
#define HEX_REG_SP   HEX_REG_ALIAS_SP
#define HEX_REG_FP   HEX_REG_ALIAS_FP
#define HEX_REG_LC0   HEX_REG_ALIAS_LC0
#define HEX_REG_SA1   HEX_REG_ALIAS_SA1
#define HEX_REG_LC1   HEX_REG_ALIAS_LC1
#define HEX_REG_P3_0   HEX_REG_ALIAS_P3_0
#define HEX_REG_M0   HEX_REG_ALIAS_M0
#define HEX_REG_M1   HEX_REG_ALIAS_M1
#define HEX_REG_USR   HEX_REG_ALIAS_USR
#define HEX_REG_PC   HEX_REG_ALIAS_PC
#define HEX_REG_UGP   HEX_REG_ALIAS_UGP
#define HEX_REG_GP   HEX_REG_ALIAS_GP
#define HEX_REG_CS0   HEX_REG_ALIAS_CS0
#define HEX_REG_CS1   HEX_REG_ALIAS_CS1
#define HEX_REG_UPCYCLELO   HEX_REG_ALIAS_UPCYCLELO
#define HEX_REG_UPCYCLEHI   HEX_REG_ALIAS_UPCYCLEHI
#define HEX_REG_FRAMELIMIT   HEX_REG_ALIAS_FRAMELIMIT
#define HEX_REG_FRAMEKEY   HEX_REG_ALIAS_FRAMEKEY
#define HEX_REG_PKTCNTLO   HEX_REG_ALIAS_PKTCNTLO
#define HEX_REG_PKTCNTHI   HEX_REG_ALIAS_PKTCNTHI
#define HEX_REG_UTIMERLO   HEX_REG_ALIAS_UTIMERLO
#define HEX_REG_UTIMERHI   HEX_REG_ALIAS_UTIMERHI
/* Use reserved control registers for qemu execution counts */
// HEX_REG_QEMU_PKT_CNT      = 52,
// HEX_REG_QEMU_INSN_CNT     = 53,
// HEX_REG_QEMU_HVX_CNT      = 54,

#define ALIAS_NEW_VAL(A) A##_NEW

#define fREAD_NPC() (get_npc(pkt) & (0xfffffffe))

// Set/get register fields

#define GET_USR_FIELD(FIELD) \
    fEXTRACTU_BITS(HEX_REG_ALIAS_USR, REGFIELD(RF_WIDTH, HEX_REG_FIELD_##FIELD), \
                   REGFIELD(RF_OFFSET, HEX_REG_FIELD_##FIELD))

#define GET_FIELD(FIELD, REGIN) \
    fEXTRACTU_BITS(REGIN, REGFIELD(RF_WIDTH, HEX_REG_FIELD_##FIELD), \
                   REGFIELD(RF_OFFSET, HEX_REG_FIELD_##FIELD))

#define SET_USR_FIELD(FIELD, VAL) \
    fINSERT_BITS(ALIAS_NEW_VAL(HEX_REG_ALIAS_USR), REGFIELD(RF_WIDTH, HEX_REG_FIELD_##FIELD), \
                 REGFIELD(RF_OFFSET, HEX_REG_FIELD_##FIELD), (VAL))

#define fALIGN_REG_FIELD_VALUE(FIELD, VAL) \
    ((VAL) << REGFIELD(RF_OFFSET, HEX_REG_FIELD_##FIELD))

#define fGET_REG_FIELD_MASK(FIELD) \
    (((1 << REGFIELD(RF_WIDTH, HEX_REG_FIELD_##FIELD)) - 1) << REGFIELD(RF_OFFSET, HEX_REG_FIELD_##FIELD))

#define fREAD_REG_FIELD(REG, FIELD) \
    fEXTRACTU_BITS(READ_REG(REG), \
                   REGFIELD(RF_WIDTH, HEX_REG_FIELD_##FIELD), \
                   REGFIELD(RF_OFFSET, HEX_REG_FIELD_##FIELD))

// New values

#define fLSBNEW0        (ALIAS_NEW_VAL(P0) & 1)
#define fLSBNEW1        (ALIAS_NEW_VAL(P1) & 1)

// Macros defined inside #QEMU_GENERATE guards without an #else.
// We do not include them in the preprocessing
// so we add them here manually.

#define PRED_LOAD_CANCEL(PRED, EA) \
    gen_pred_cancel(PRED, insn->is_endloop ? 4 : insn->slot)
#define fLOAD_LOCKED(NUM, SIZE, SIGN, EA, DST) \
    gen_load_locked##SIZE##SIGN(DST, EA, ctx->mem_idx);
#define fSTORE_LOCKED(NUM, SIZE, EA, SRC, PRED) \
    gen_store_conditional##SIZE(ctx, PRED, EA, SRC);

// Frame checks are currently not implemented. They are not modeled for user instructions anyway.
#define fFRAMECHECK(ADDR, EA)

// TODO
// fCARRY_FROM_ADD
// fEA_BREVR
// fPM_CIRI
// fPM_CIRR
// fCARRY_FROM_ADD
// fFLOAT
// fSF_RECIP_COMMON
// fSF_INVSQRT_COMMON
// fDOUBLE
