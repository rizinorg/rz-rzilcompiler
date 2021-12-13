
Instructionndefinition -> IDEF uses macros defined to convert common operations to code (e.g. get word of reg).
Scanner sees macros from definitions and converts sets yy attributes.

We need to adapt the scanner to parse our C code instead of those macros.


Q6INSN(A2_vcmpwgtu,"Pd4=vcmpw.gtu(Rss32,Rtt32)",ATTRIBS(),
"Compare elements of two vectors ",
{
    fSETBITS(3,0,PdV,(fGETUWORD(0,RssV)>fGETUWORD(0,RttV)));
    fSETBITS(7,4,PdV,(fGETUWORD(1,RssV)>fGETUWORD(1,RttV)));
})

DEF_MACRO(fSETBITS,
    do {
        int j;
        for (j=LO;j<=HI;j++) {
          fSETBIT(j,DST,VAL);
        }
    } while (0),
    /* nothing */
)


DEF_MACRO(fGETUWORD,
    ((size8u_t)((size4u_t)((SRC>>((N)*32))&0x0ffffffffLL))),
    /* nothing */
)
MNAME = mnemonic name?
BEH = Behavior
ATTR = Attributes
#define DEF_MACRO(MNAME, BEH, ATTRS) \
    fprintf(outfile, "MACROATTRIB( \\\n" \
                     "    \"%s\", \\\n" \
                     "    \"\"\"%s\"\"\", \\\n" \
                     "    \"%s\" \\\n" \
                     ")\n", \
            #MNAME, STRINGIZE(BEH), STRINGIZE(ATTRS));
