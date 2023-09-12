int high_half[SIZE];

int main()
{
    void *p;

    for (int i = 0; i < SIZE; i++) {
        bbuf[i] = bitreverse(i);
        hbuf[i] = bitreverse(i);
        wbuf[i] = bitreverse(i);
        dbuf[i] = bitreverse(i);
        high_half[i] = i << 16;
    }

    TEST_BREV_LOAD(b,  int32_t,   bbuf, 16, sext8(i));
    TEST_BREV_LOAD(ub, int32_t,   bbuf, 16, i);
    TEST_BREV_LOAD(h,  int32_t,   hbuf, 15, i);
    TEST_BREV_LOAD(uh, int32_t,   hbuf, 15, i);
    TEST_BREV_LOAD(w,  int32_t,   wbuf, 14, i);
    TEST_BREV_LOAD(d,  int64_t,   dbuf, 13, i);

    TEST_BREV_STORE(b, int32_t,   bbuf, i,            16);
    TEST_BREV_STORE(h, int32_t,   hbuf, i,            15);
    TEST_BREV_STORE(f, int32_t,   hbuf, high_half[i], 15);
    TEST_BREV_STORE(w, int32_t,   wbuf, i,            14);
    TEST_BREV_STORE(d, int64_t,   dbuf, i,            13);

    TEST_BREV_STORE_NEW(bnew, bbuf, 16);
    TEST_BREV_STORE_NEW(hnew, hbuf, 15);
    TEST_BREV_STORE_NEW(wnew, wbuf, 14);

    puts(err ? "FAIL" : "PASS");
    return err ? 1 : 0;
}
