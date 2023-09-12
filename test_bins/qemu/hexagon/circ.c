#define CHECK_STORE(SZ, BUF, BUFSIZE, FMT) \
void check_store_##SZ(int32_t inc, int32_t size) \
{ \
    for (int i = 0; i < size; i++) { \
        DEBUG_PRINTF(#BUF "[%3d] = 0x%02" #FMT ", guess = 0x%02" #FMT "\n", \
                     i, BUF[i], circ_val_##SZ(i, inc, size)); \
        check64(BUF[i], circ_val_##SZ(i, inc, size)); \
    } \
    for (int i = size; i < BUFSIZE; i++) { \
        check64(BUF[i], i); \
    } \
}

CHECK_STORE(b, bbuf, NBYTES, x)
CHECK_STORE(h, hbuf, NHALFS, x)
CHECK_STORE(w, wbuf, NWORDS, x)
CHECK_STORE(d, dbuf, NDOBLS, llx)

#define CIRC_TEST_STORE_IMM(SZ, CHK, TYPE, BUF, BUFSIZE, SHIFT, INC) \
void circ_test_store_imm_##SZ(void) \
{ \
    uint32_t size = 27; \
    TYPE *p = BUF; \
    TYPE val = 0; \
    init_##BUF(); \
    for (int i = 0; i < BUFSIZE; i++) { \
        CIRC_STORE_IMM_##SZ(val << SHIFT, p, BUF, size * sizeof(TYPE), INC); \
        val++; \
    } \
    check_store_##CHK(((INC) / (int)sizeof(TYPE)), size); \
    p = BUF; \
    val = 0; \
    init_##BUF(); \
    for (int i = 0; i < BUFSIZE; i++) { \
        CIRC_STORE_IMM_##SZ(val << SHIFT, p, BUF, size * sizeof(TYPE), \
                            -(INC)); \
        val++; \
    } \
    check_store_##CHK((-(INC) / (int)sizeof(TYPE)), size); \
}

CIRC_TEST_STORE_IMM(b,    b, uint8_t,       bbuf, NBYTES, 0,  1)
CIRC_TEST_STORE_IMM(h,    h, int16_t,       hbuf, NHALFS, 0,  2)
CIRC_TEST_STORE_IMM(f,    h, int16_t,       hbuf, NHALFS, 16, 2)
CIRC_TEST_STORE_IMM(w,    w, int32_t,       wbuf, NWORDS, 0,  4)
CIRC_TEST_STORE_IMM(d,    d, int64_t,       dbuf, NDOBLS, 0,  8)
CIRC_TEST_STORE_IMM(bnew, b, uint8_t,       bbuf, NBYTES, 0,  1)
CIRC_TEST_STORE_IMM(hnew, h, int16_t,       hbuf, NHALFS, 0,  2)
CIRC_TEST_STORE_IMM(wnew, w, int32_t,       wbuf, NWORDS, 0,  4)

#define CIRC_TEST_STORE_REG(SZ, CHK, TYPE, BUF, BUFSIZE, SHIFT) \
void circ_test_store_reg_##SZ(void) \
{ \
    TYPE *p = BUF; \
    uint32_t size = 19; \
    TYPE val = 0; \
    init_##BUF(); \
    for (int i = 0; i < BUFSIZE; i++) { \
        CIRC_STORE_REG_##SZ(val << SHIFT, p, BUF, size * sizeof(TYPE), 1); \
        val++; \
    } \
    check_store_##CHK(1, size); \
    p = BUF; \
    val = 0; \
    init_##BUF(); \
    for (int i = 0; i < BUFSIZE; i++) { \
        CIRC_STORE_REG_##SZ(val << SHIFT, p, BUF, size * sizeof(TYPE), -1); \
        val++; \
    } \
    check_store_##CHK(-1, size); \
}

CIRC_TEST_STORE_REG(b,    b, uint8_t,       bbuf, NBYTES, 0)
CIRC_TEST_STORE_REG(h,    h, int16_t,       hbuf, NHALFS, 0)
CIRC_TEST_STORE_REG(f,    h, int16_t,       hbuf, NHALFS, 16)
CIRC_TEST_STORE_REG(w,    w, int32_t,       wbuf, NWORDS, 0)
CIRC_TEST_STORE_REG(d,    d, int64_t,       dbuf, NDOBLS, 0)
CIRC_TEST_STORE_REG(bnew, b, uint8_t,       bbuf, NBYTES, 0)
CIRC_TEST_STORE_REG(hnew, h, int16_t,       hbuf, NHALFS, 0)
CIRC_TEST_STORE_REG(wnew, w, int32_t,       wbuf, NWORDS, 0)

/* Test the old scheme used in Hexagon V3 */
static void circ_test_v3(void)
{
    int *p = wbuf;
    int32_t size = 15;
    /* set high bit in K to test unsigned extract in fcirc */
    int32_t K = 8;      /* 1024 bytes */
    int32_t element;

    init_wbuf();

    for (int i = 0; i < NWORDS; i++) {
        __asm__(
            "r4 = %2\n\t"
            "m1 = r4\n\t"
            "%0 = memw(%1++I:circ(M1))\n\t"
            : "=r"(element), "+r"(p)
            : "r"(build_mreg(1, K, size * sizeof(int)))
            : "r4", "m1");
        DEBUG_PRINTF("i = %2d, p = 0x%p, element = %2d\n", i, p, element);
        check_load(i, element, 1, size);
    }
}

int main()
{
    init_bbuf();
    init_hbuf();
    init_wbuf();
    init_dbuf();

    DEBUG_PRINTF("NBYTES = %d\n", NBYTES);
    DEBUG_PRINTF("Address of dbuf = 0x%p\n", dbuf);
    DEBUG_PRINTF("Address of wbuf = 0x%p\n", wbuf);
    DEBUG_PRINTF("Address of hbuf = 0x%p\n", hbuf);
    DEBUG_PRINTF("Address of bbuf = 0x%p\n", bbuf);

    circ_test_load_imm_b();
    circ_test_load_imm_ub();
    circ_test_load_imm_h();
    circ_test_load_imm_uh();
    circ_test_load_imm_w();
    circ_test_load_imm_d();

    circ_test_load_reg_b();
    circ_test_load_reg_ub();
    circ_test_load_reg_h();
    circ_test_load_reg_uh();
    circ_test_load_reg_w();
    circ_test_load_reg_d();

    circ_test_store_imm_b();
    circ_test_store_imm_h();
    circ_test_store_imm_f();
    circ_test_store_imm_w();
    circ_test_store_imm_d();
    circ_test_store_imm_bnew();
    circ_test_store_imm_hnew();
    circ_test_store_imm_wnew();

    circ_test_store_reg_b();
    circ_test_store_reg_h();
    circ_test_store_reg_f();
    circ_test_store_reg_w();
    circ_test_store_reg_d();
    circ_test_store_reg_bnew();
    circ_test_store_reg_hnew();
    circ_test_store_reg_wnew();

    circ_test_v3();

    puts(err ? "FAIL" : "PASS");
    return err ? 1 : 0;
}
