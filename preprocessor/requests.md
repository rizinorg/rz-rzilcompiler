- Makros like `sxt128->64` should become `sxt128_64`.
- Remove additional white space from macros: `zxt 5->32` should become `zxt5->32`.
- Remove brackets indicating possible syntax: `[!]`, `[.new]`, `[sat32]`, `[&|]` as in `Qx4[&|]=vcmp.eq(Vu.b,Vv.b)`.
  - Substitution is only ncessary if in both (Sytax and Behavior) [] occure
- Remove "" in certain if statements. As in: `if ("((#m9<0) && (#m9>-256))") {`
- Missing ; before `if` after a tenary expression. Example in this behavior :
```
p[01]=cmp.eq(Rs,#-1); if              P[01]=(Rs==-1) ? 0xff : 0x00 if    <-------- Here
([!]p[01].new) jump:<hint>            ([!]P[01].new[0]) {
#r9:2                                     apply_extension(#r);
                                          #r=#r & ~PCALIGN_MASK;
                                          PC=PC+#r;
                                      }

```
