static void SL2_return_tnew(bool pred);
asm ("SL2_return_tnew:\n\t"
     "   allocframe(#0)\n\t"
     "   r1 = #1\n\t"
     "   memw(##early_exit) = r1\n\t"
     "   {\n\t"
     "       p0 = cmp.eq(r0, #1)\n\t"
     "       if (p0.new) dealloc_return:nt\n\t"    /* SL2_return_tnew */
     "   }\n\t"
     "   r1 = #0\n\t"
     "   memw(##early_exit) = r1\n\t"
     "   dealloc_return\n\t"
    );

static int64_t creg_pair(int32_t x, int32_t y)
{
    int64_t retval;
    asm ("m0 = %1\n\t"
         "m1 = %2\n\t"
         "%0 = c7:6\n\t"
         : "=r"(retval) : "r"(x), "r"(y) : "m0", "m1");
    return retval;
}

#if CORE_HAS_CABAC
static int64_t decbin(int64_t x, int64_t y, bool *pred)
{
    int64_t retval;
    asm ("%0 = decbin(%2, %3)\n\t"
         "%1 = p0\n\t"
         : "=r"(retval), "=r"(*pred)
         : "r"(x), "r"(y));
    return retval;
}
#endif

/* Check that predicates are auto-and'ed in a packet */
static bool auto_and(void)
{
    bool retval;
    asm ("r5 = #1\n\t"
         "{\n\t"
         "    p0 = cmp.eq(r1, #1)\n\t"
         "    p0 = cmp.eq(r1, #2)\n\t"
         "}\n\t"
         "%0 = p0\n\t"
         : "=r"(retval)
         :
         : "r5", "p0");
    return retval;
}

void test_lsbnew(void)
{
    int32_t result;

    asm("r0 = #2\n\t"
        "r1 = #5\n\t"
        "{\n\t"
        "    p0 = r0\n\t"
        "    if (p0.new) r1 = #3\n\t"
        "}\n\t"
        "%0 = r1\n\t"
        : "=r"(result) :: "r0", "r1", "p0");
    check32(result, 5);
}

void test_l2fetch(void)
{
    /* These don't do anything in qemu, just make sure they don't assert */
    asm volatile ("l2fetch(r0, r1)\n\t"
                  "l2fetch(r0, r3:2)\n\t");
}

static inline int32_t ct0(uint32_t x)
{
    int32_t res;
    asm("%0 = ct0(%1)\n\t" : "=r"(res) : "r"(x));
    return res;
}

static inline int32_t ct1(uint32_t x)
{
    int32_t res;
    asm("%0 = ct1(%1)\n\t" : "=r"(res) : "r"(x));
    return res;
}

static inline int32_t ct0p(uint64_t x)
{
    int32_t res;
    asm("%0 = ct0(%1)\n\t" : "=r"(res) : "r"(x));
    return res;
}

static inline int32_t ct1p(uint64_t x)
{
    int32_t res;
    asm("%0 = ct1(%1)\n\t" : "=r"(res) : "r"(x));
    return res;
}

void test_count_trailing_zeros_ones(void)
{
    check32(ct0(0x0000000f), 0);
    check32(ct0(0x00000000), 32);
    check32(ct0(0x000000f0), 4);

    check32(ct1(0x000000f0), 0);
    check32(ct1(0x0000000f), 4);
    check32(ct1(0x00000000), 0);
    check32(ct1(0xffffffff), 32);

    check32(ct0p(0x000000000000000fULL), 0);
    check32(ct0p(0x0000000000000000ULL), 64);
    check32(ct0p(0x00000000000000f0ULL), 4);

    check32(ct1p(0x00000000000000f0ULL), 0);
    check32(ct1p(0x000000000000000fULL), 4);
    check32(ct1p(0x0000000000000000ULL), 0);
    check32(ct1p(0xffffffffffffffffULL), 64);
    check32(ct1p(0xffffffffff0fffffULL), 20);
    check32(ct1p(0xffffff0fffffffffULL), 36);
}

static inline int32_t dpmpyss_rnd_s0(int32_t x, int32_t y)
{
    int32_t res;
    asm("%0 = mpy(%1, %2):rnd\n\t" : "=r"(res) : "r"(x), "r"(y));
    return res;
}

void test_dpmpyss_rnd_s0(void)
{
    check32(dpmpyss_rnd_s0(-1, 0x80000000), 1);
    check32(dpmpyss_rnd_s0(0, 0x80000000), 0);
    check32(dpmpyss_rnd_s0(1, 0x80000000), 0);
    check32(dpmpyss_rnd_s0(0x7fffffff, 0x80000000), 0xc0000001);
    check32(dpmpyss_rnd_s0(0x80000000, -1), 1);
    check32(dpmpyss_rnd_s0(-1, -1), 0);
    check32(dpmpyss_rnd_s0(0, -1), 0);
    check32(dpmpyss_rnd_s0(1, -1), 0);
    check32(dpmpyss_rnd_s0(0x7fffffff, -1), 0);
    check32(dpmpyss_rnd_s0(0x80000000, 0), 0);
    check32(dpmpyss_rnd_s0(-1, 0), 0);
    check32(dpmpyss_rnd_s0(0, 0), 0);
    check32(dpmpyss_rnd_s0(1, 0), 0);
    check32(dpmpyss_rnd_s0(-1, -1), 0);
    check32(dpmpyss_rnd_s0(0, -1), 0);
    check32(dpmpyss_rnd_s0(1, -1), 0);
    check32(dpmpyss_rnd_s0(0x7fffffff, 1), 0);
    check32(dpmpyss_rnd_s0(0x80000000, 0x7fffffff), 0xc0000001);
    check32(dpmpyss_rnd_s0(-1, 0x7fffffff), 0);
    check32(dpmpyss_rnd_s0(0, 0x7fffffff),  0);
    check32(dpmpyss_rnd_s0(1, 0x7fffffff),  0);
    check32(dpmpyss_rnd_s0(0x7fffffff, 0x7fffffff), 0x3fffffff);
}

int main()
{
    int32_t res;
    int64_t res64;
    bool pred;

    memcpy(array, init, sizeof(array));
    S4_storerhnew_rr(array, 4, 0xffff);
    check32(array[4], 0xffff);

    data = ~0;
    checkp(S4_storerbnew_ap(0x12), &data);
    check32(data, 0xffffff12);

    data = ~0;
    checkp(S4_storerhnew_ap(0x1234), &data);
    check32(data, 0xffff1234);

    data = ~0;
    checkp(S4_storerinew_ap(0x12345678), &data);
    check32(data, 0x12345678);

    /* Byte */
    memcpy(array, init, sizeof(array));
    S4_storeirbt_io(&array[1], true);
    check32(array[2], 27);
    S4_storeirbt_io(&array[2], false);
    check32(array[3], 3);

    memcpy(array, init, sizeof(array));
    S4_storeirbf_io(&array[3], false);
    check32(array[4], 27);
    S4_storeirbf_io(&array[4], true);
    check32(array[5], 5);

    memcpy(array, init, sizeof(array));
    S4_storeirbtnew_io(&array[5], true);
    check32(array[6], 27);
    S4_storeirbtnew_io(&array[6], false);
    check32(array[7], 7);

    memcpy(array, init, sizeof(array));
    S4_storeirbfnew_io(&array[7], false);
    check32(array[8], 27);
    S4_storeirbfnew_io(&array[8], true);
    check32(array[9], 9);

    /* Half word */
    memcpy(array, init, sizeof(array));
    S4_storeirht_io(&array[1], true);
    check32(array[2], 27);
    S4_storeirht_io(&array[2], false);
    check32(array[3], 3);

    memcpy(array, init, sizeof(array));
    S4_storeirhf_io(&array[3], false);
    check32(array[4], 27);
    S4_storeirhf_io(&array[4], true);
    check32(array[5], 5);

    memcpy(array, init, sizeof(array));
    S4_storeirhtnew_io(&array[5], true);
    check32(array[6], 27);
    S4_storeirhtnew_io(&array[6], false);
    check32(array[7], 7);

    memcpy(array, init, sizeof(array));
    S4_storeirhfnew_io(&array[7], false);
    check32(array[8], 27);
    S4_storeirhfnew_io(&array[8], true);
    check32(array[9], 9);

    /* Word */
    memcpy(array, init, sizeof(array));
    S4_storeirit_io(&array[1], true);
    check32(array[2], 27);
    S4_storeirit_io(&array[2], false);
    check32(array[3], 3);

    memcpy(array, init, sizeof(array));
    S4_storeirif_io(&array[3], false);
    check32(array[4], 27);
    S4_storeirif_io(&array[4], true);
    check32(array[5], 5);

    memcpy(array, init, sizeof(array));
    S4_storeiritnew_io(&array[5], true);
    check32(array[6], 27);
    S4_storeiritnew_io(&array[6], false);
    check32(array[7], 7);

    memcpy(array, init, sizeof(array));
    S4_storeirifnew_io(&array[7], false);
    check32(array[8], 27);
    S4_storeirifnew_io(&array[8], true);
    check32(array[9], 9);

    memcpy(array, init, sizeof(array));
    res = L2_ploadrifnew_pi(&array[6], false);
    check32(res, 6);
    res = L2_ploadrifnew_pi(&array[7], true);
    check32(res, 31);

    res = cmpnd_cmp_jump();
    check32(res, 12);

    SL2_return_tnew(false);
    check32(early_exit, false);
    SL2_return_tnew(true);
    check32(early_exit, true);

    res64 = creg_pair(5, 7);
    check32((int32_t)res64, 5);
    check32((int32_t)(res64 >> 32), 7);

    res = test_clrtnew(1, 7);
    check32(res, 0);
    res = test_clrtnew(2, 7);
    check32(res, 7);

#if CORE_HAS_CABAC
    res64 = decbin(0xf0f1f2f3f4f5f6f7LL, 0x7f6f5f4f3f2f1f0fLL, &pred);
    check64(res64, 0x357980003700010cLL);
    check32(pred, false);

    res64 = decbin(0xfLL, 0x1bLL, &pred);
    check64(res64, 0x78000100LL);
    check32(pred, true);
#else
    puts("Skipping cabac tests");
#endif

    pred = auto_and();
    check32(pred, false);

    test_lsbnew();

    test_l2fetch();

    test_count_trailing_zeros_ones();

    test_dpmpyss_rnd_s0();

    puts(err ? "FAIL" : "PASS");
    return err;
}
