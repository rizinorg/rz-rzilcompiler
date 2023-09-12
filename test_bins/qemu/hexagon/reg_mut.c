
#define PC_EQ_R0        ".word 0x6220c009"
#define C9_8_EQ_R1_0    ".word 0x6320c008"

static inline void write_control_registers(void)
{
    uint32_t result = 0;

    WRITE_REG_NOCLOBBER(result, "usr", 0xffffffff);
    check32(result, 0x3ecfff3f);

    WRITE_REG_NOCLOBBER(result, "gp", 0xffffffff);
    check32(result, 0xffffffc0);

    WRITE_REG_NOCLOBBER(result, "upcyclelo", 0xffffffff);
    check32(result, 0x00000000);

    WRITE_REG_NOCLOBBER(result, "upcyclehi", 0xffffffff);
    check32(result, 0x00000000);

    WRITE_REG_NOCLOBBER(result, "utimerlo", 0xffffffff);
    check32(result, 0x00000000);

    WRITE_REG_NOCLOBBER(result, "utimerhi", 0xffffffff);
    check32(result, 0x00000000);

    /*
     * PC is special.  Setting it to these values
     * should cause a catastrophic failure.
     */
    WRITE_REG_ENCODED(result, "pc", 0x00000000, PC_EQ_R0);
    check32_ne(result, 0x00000000);

    WRITE_REG_ENCODED(result, "pc", 0x00000001, PC_EQ_R0);
    check32_ne(result, 0x00000001);

    WRITE_REG_ENCODED(result, "pc", 0xffffffff, PC_EQ_R0);
    check32_ne(result, 0xffffffff);
}

static inline void write_control_register_pairs(void)
{
    uint64_t result = 0;

    WRITE_REG_NOCLOBBER(result, "c11:10", 0xffffffffffffffff);
    check64(result, 0xffffffc0ffffffff);

    WRITE_REG_NOCLOBBER(result, "c15:14", 0xffffffffffffffff);
    check64(result, 0x0000000000000000);

    WRITE_REG_NOCLOBBER(result, "c31:30", 0xffffffffffffffff);
    check64(result, 0x0000000000000000);

    WRITE_REG_PAIR_ENCODED(result, "c9:8", (uint64_t) 0x0000000000000000,
                           C9_8_EQ_R1_0);
    check64_ne(result, 0x000000000000000);

    WRITE_REG_PAIR_ENCODED(result, "c9:8", 0x0000000100000000, C9_8_EQ_R1_0);
    check64_ne(result, 0x0000000100000000);

    WRITE_REG_PAIR_ENCODED(result, "c9:8", 0xffffffffffffffff, C9_8_EQ_R1_0);
    check64_ne(result, 0xffffffffffffffff);
}

int main()
{
    err = 0;

    write_control_registers();
    write_control_register_pairs();

    puts(err ? "FAIL" : "PASS");
    return err;
}
