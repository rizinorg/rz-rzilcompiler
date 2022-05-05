behaviors = [
    """
        i = 4*i+4-1;
        """,
    """
        i = 4+i*4-1;
        """,
    """
        sumr = 0;
sumi = 0;
control = Rt.ub[#u];
for (i = 0; i < 8; i += 2) {
tmpr = Rss.b[i];
tmpi = Rss.b[i+1];
switch (control & 3) {
case 0: sumr += tmpr;
sumi += tmpi;
break;
case 1: sumr += tmpi;
sumi -= tmpr;
break;
case 2: sumr -= tmpi;
sumi += tmpr;
break;
case 3: sumr -= tmpr;
sumi -= tmpi;
break;
}
control = control >> 2;
}
Rdd.w[0]=sumr;
Rdd.w[1]=sumi;
        """,
    """
        if (CHECK_TLB_OVERLAP((1LL<<63) | Rss)) {
Rd=GET_OVERLAPPING_IDX((1LL<<63) | Rss);
} else {
Rd=0x80000000;
}
        """,
    """
        for (i = 0; i < NUM_TLB_ENTRIES; i++) {
if ((TLB[i] == 0) && (TLB[i] == Rs[26:20])) {
TLB[i] = TLB[i] & ~(1ULL << 63);
}
}

        """,
    """
        if (((#m9<0) && (#m9>-256))) {
Assembler mapped to: "Rd=-mpyi(Rs,#m9*(-1))";
} else {
Assembler mapped to: "Rd=+mpyi(Rs,#m9)";
}
""",
    """
        QeV[4*i+4-1] = 1;
        """,
    """
        if (#u == 0) {
Rdd = Rss;
} else if ((Rss & (size8s_t)((1LL << (#u - 1)) - 1LL)) == 0) {
src_128 = sxt64_128(Rss);
rndbit_128 = sxt64_128(1LL);
rndbit_128 = (rndbit_128 << #u);
rndbit_128 = (rndbit_128 & src_128);
rndbit_128 = (size8s_t) (rndbit_128 >> 1);
tmp128 = src_128+rndbit_128;
tmp128 = (size8s_t) (tmp128 >> #u);
Rdd = sxt128_64(tmp128);
} else {
size16s_t rndbit_128 = sxt64_128((1LL << (#u
- 1)));
size16s_t src_128 = sxt64_128(Rss);
size16s_t tmp128 = src_128+rndbit_128;
tmp128 = (size8s_t) (tmp128 >> #u);
Rdd = sxt128_64(tmp128);
}
;
;
        """,
    """
        Rd = (sat_32((#u==0)?(Rs):round(Rs,2**(#u-
1))))>>#u;
        """,
    """
        Rd = (zxt5_32(Rt)==0)?Rs:convround(Rs,2**(zxt5_32 (Rt)-1))>>zxt5_32(Rt);
        """,
    """
        Rd = (#u==0)?Rs:convround(Rs,2**(#u-1))>>#u;
        """,
    """
        Rd = sat_32(-Rs.s64);
        """,
    """
        apply_extension(#s);
Rx=Rx - (Rs + #s);
        """,
    """
        l2fetch(Rs,INFO);
        """,
    """
        dcache_tag_write(Rs,Rt);
        """,
    """
        EA=Rx;
if (!Pv.new[0]){
Rx=Rx+#s;
*EA = Rt.h[1];
} else {
NOP;
}
        """,
    """
        for (i=0;i<2;i++) {
Rdd.w[i]=(Rss.uw[i]>>#u);
}
        """,
    """
        for (i = 0; i < VELEM(32); i++) {
Vd.w[i] = Vu.w[i]+~Vv.w[i]+QxV[i*4];
QxV[4*i+4-1:4*i] = -
carry_from(Vu.w[i],~Vv.w[i],QxV[i*4]) ;
}
        """,
    """
        Rdd = -Rss;
        """,
    """
        Rd = max(Rs.uw[0],Rt.uw[0]);
        """,
    """
        ;
        if (!(Ns.new.uw[0]>(#U))) {
        apply_extension(#r);
        #r=#r & ~PCALIGN_MASK;
        PC=PC+#r;
        }
        """,
    """
        for (i = 0; i < VELEM(32); i++) {
Vd.w[i] = Vu.w[i]+Vv.w[i];
QeV[4*i+4-1:4*i] = -
carry_from(Vu.w[i],Vv.w[i],0) ;
}
        """,
]
