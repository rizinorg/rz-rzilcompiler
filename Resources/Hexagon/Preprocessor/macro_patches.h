// SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
// SPDX-License-Identifier: LGPL-3.0-only

// Macros in this file fill replace the qualcomm macros from the Qemu source.

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

#define fIMMEXT(IMM)

#define fREAD_GP() \
    (insn->extension_valid ? 0 : READ_REG(HEX_REG_GP))
#define fWRITE_NPC(A) JUMP(A)

#define READ_REG(NUM)                    R##NUM
#define READ_PREG(NUM)                   P##NUM
#define fREAD_GP() GP
#define fREAD_PC() pc
