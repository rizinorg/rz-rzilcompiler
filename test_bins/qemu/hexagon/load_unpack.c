#define BxW_LOAD_pcr(SZ, RES, PTR, START, LEN, INC) \
    __asm__( \
        "r4 = %2\n\t" \
        "m1 = r4\n\t" \
        "cs1 = %3\n\t" \
        "%0 = mem" #SZ "(%1++I:circ(m1))\n\t" \
        : "=r"(RES), "+r"(PTR) \
        : "r"((((INC) & 0x7f) << 17) | ((LEN) & 0x1ffff)), \
          "r"(START) \
        : "r4", "m1", "cs1")
#define BxW_LOAD_pcr_Z(RES, PTR, START, LEN, INC) \
    BxW_LOAD_pcr(ubh, RES, PTR, START, LEN, INC)
#define BxW_LOAD_pcr_S(RES, PTR, START, LEN, INC) \
    BxW_LOAD_pcr(bh, RES, PTR, START, LEN, INC)

#define TEST_pcr(NAME, TYPE, SIGN, SIZE, LEN, INC, \
                 EXT, RES1, RES2, RES3, RES4) \
void test_##NAME(void) \
{ \
    TYPE result; \
    void *ptr = buf; \
    init_buf(); \
    BxW_LOAD_pcr_##SIGN(result, ptr, buf, (LEN), (INC)); \
    check64(result, (RES1) | (EXT)); \
    checkp(ptr, &buf[(1 * (INC) * (SIZE)) % (LEN)]); \
    BxW_LOAD_pcr_##SIGN(result, ptr, buf, (LEN), (INC)); \
    check64(result, (RES2) | (EXT)); \
    checkp(ptr, &buf[(2 * (INC) * (SIZE)) % (LEN)]); \
    BxW_LOAD_pcr_##SIGN(result, ptr, buf, (LEN), (INC)); \
    check64(result, (RES3) | (EXT)); \
    checkp(ptr, &buf[(3 * (INC) * (SIZE)) % (LEN)]); \
    BxW_LOAD_pcr_##SIGN(result, ptr, buf, (LEN), (INC)); \
    check64(result, (RES4) | (EXT)); \
    checkp(ptr, &buf[(4 * (INC) * (SIZE)) % (LEN)]); \
}

TEST_pcr(loadbzw2_pcr, int32_t, Z, 2, 8, 2, 0x00000000,
    0x00020081, 0x00060085, 0x00020081, 0x00060085)
TEST_pcr(loadbsw2_pcr, int32_t, S, 2, 8, 2, 0x0000ff00,
    0x00020081, 0x00060085, 0x00020081, 0x00060085)
TEST_pcr(loadbzw4_pcr, int64_t, Z, 4, 8, 1, 0x0000000000000000LL,
    0x0004008300020081LL, 0x0008008700060085LL,
    0x0004008300020081LL, 0x0008008700060085LL)
TEST_pcr(loadbsw4_pcr, int64_t, S, 4, 8, 1, 0x0000ff000000ff00LL,
    0x0004008300020081LL, 0x0008008700060085LL,
    0x0004008300020081LL, 0x0008008700060085LL)

int main()
{
    test_loadbzw2_io();
    test_loadbsw2_io();
    test_loadbzw4_io();
    test_loadbsw4_io();

    test_loadbzw2_ur();
    test_loadbsw2_ur();
    test_loadbzw4_ur();
    test_loadbsw4_ur();

    test_loadbzw2_ap();
    test_loadbsw2_ap();
    test_loadbzw4_ap();
    test_loadbsw4_ap();

    test_loadbzw2_pr();
    test_loadbsw2_pr();
    test_loadbzw4_pr();
    test_loadbsw4_pr();

    test_loadbzw2_pbr();
    test_loadbsw2_pbr();
    test_loadbzw4_pbr();
    test_loadbsw4_pbr();

    test_loadbzw2_pi();
    test_loadbsw2_pi();
    test_loadbzw4_pi();
    test_loadbsw4_pi();

    test_loadbzw2_pci();
    test_loadbsw2_pci();
    test_loadbzw4_pci();
    test_loadbsw4_pci();

    test_loadbzw2_pcr();
    test_loadbsw2_pcr();
    test_loadbzw4_pcr();
    test_loadbsw4_pcr();

    puts(err ? "FAIL" : "PASS");
    return err ? 1 : 0;
}
