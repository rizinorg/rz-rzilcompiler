#define LOAD_pcr(SZ, RES, PTR, START, LEN, INC) \
    __asm__( \
        "r4 = %2\n\t" \
        "m1 = r4\n\t" \
        "cs1 = %3\n\t" \
        "%0 = mem" #SZ "_fifo(%1++I:circ(m1))\n\t" \
        : "+r"(RES), "+r"(PTR) \
        : "r"((((INC) & 0x7f) << 17) | ((LEN) & 0x1ffff)), \
          "r"(START) \
        : "r4", "m1", "cs1")
#define LOAD_pcr_b(RES, PTR, START, LEN, INC) \
    LOAD_pcr(b, RES, PTR, START, LEN, INC)
#define LOAD_pcr_h(RES, PTR, START, LEN, INC) \
    LOAD_pcr(h, RES, PTR, START, LEN, INC)

#define TEST_pcr(NAME, SZ, SIZE, LEN, INC, RES1, RES2, RES3, RES4) \
void test_##NAME(void) \
{ \
    int64_t result = ~0LL; \
    void *ptr = buf; \
    LOAD_pcr_##SZ(result, ptr, buf, (LEN), (INC)); \
    check64(result, (RES1)); \
    checkp(ptr, &buf[(1 * (INC) * (SIZE)) % (LEN)]); \
    LOAD_pcr_##SZ(result, ptr, buf, (LEN), (INC)); \
    check64(result, (RES2)); \
    checkp(ptr, &buf[(2 * (INC) * (SIZE)) % (LEN)]); \
    LOAD_pcr_##SZ(result, ptr, buf, (LEN), (INC)); \
    check64(result, (RES3)); \
    checkp(ptr, &buf[(3 * (INC) * (SIZE)) % (LEN)]); \
    LOAD_pcr_##SZ(result, ptr, buf, (LEN), (INC)); \
    check64(result, (RES4)); \
    checkp(ptr, &buf[(4 * (INC) * (SIZE)) % (LEN)]); \
}

TEST_pcr(loadalignb_pcr, b, 1, 2, 1,
    0x01ffffffffffffffLL, 0x0201ffffffffffffLL,
    0x010201ffffffffffLL, 0x02010201ffffffffLL)
TEST_pcr(loadalignh_pcr, h, 2, 4, 1,
    0x0201ffffffffffffLL, 0x04030201ffffffffLL,
    0x020104030201ffffLL, 0x0403020104030201LL)

int main()
{
    init_buf();

    test_loadalignb_io();
    test_loadalignh_io();

    test_loadalignb_ur();
    test_loadalignh_ur();

    test_loadalignb_ap();
    test_loadalignh_ap();

    test_loadalignb_pr();
    test_loadalignh_pr();

    test_loadalignb_pbr();
    test_loadalignh_pbr();

    test_loadalignb_pi();
    test_loadalignh_pi();

    test_loadalignb_pci();
    test_loadalignh_pci();

    test_loadalignb_pcr();
    test_loadalignh_pcr();

    puts(err ? "FAIL" : "PASS");
    return err ? 1 : 0;
}
