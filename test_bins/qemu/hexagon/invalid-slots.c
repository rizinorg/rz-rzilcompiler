char mem[8] __attribute__((aligned(8)));

int main()
{
    asm volatile(
        "r0 = #mem\n"
        /* Invalid packet (2 instructions at slot 0): */
        ".word 0xa1804100\n" /* { memw(r0) = r1;      */
        ".word 0x28032804\n" /*   r3 = #0; r4 = #0 }  */
        : : : "r0", "r3", "r4", "memory");
    return 0;
}
