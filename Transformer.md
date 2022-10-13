```
                         ┌──────────────────────────────────────────────────────────────────────────┐
                         │ ...                                                                      │
                         │ class HexagonCompilerExtension(CompilerExtension):                       │
                         │     def transform_insn_name(self, insn_name) -> str:                     │
                         │         if "sa2_tfrsi" in insn_name.lower():                             │
                         │             # SA2_tfrsi is the sub-instruction equivalent to A2_tfrsi.   │
                         │             # But it is not documented and not in the shortcode.         │
                         │             return "A2_tfrsi"                                            │
                         │         if insn_name[:2] == "X2":                                        │
                         │ ...                                                                      │
                         └────────────────────────────────┬─────────────────────────────────────────┘
                                                          │
                                                          │
                                                          │
                                                          │ Transfomer Extension code
                                                          │
                                                          │
                                                          │
                                                          │
                                                          │
                                                          │
┌─────────────────────────┐                               │                           ┌───────────────────────────────────────────────────────────────┐
│ fbody                   │                               ▼                           │ // READ                                                       │
│   block_item            │                ┌───────────────────────────────┐          │ const char *Rd_assoc_tmp = ISA2REG(hi, 'd', true);            │
│     assignment_expr     │                │                               │          │ RzILOpPure *pc = U32(pkt->pkt_addr);                          │
│       reg               │ Parsing Tree   │                               │ RZIL     │ RzILOpPure *u = UN(32, (ut32) ISA2IMM(hi, 'u'));              │
│         R               ├───────────────►│   Transformer                 ├─────────►│                                                               │
│         d               │                │                               │          │ // EXEC                                                       │
│       =                 │                │                               │          │ RzILOpPure *op_ADD_1 = ADD(pc, VARL("u"));                    │
│       additive_expr     │                │                               │          │ RzILOpPure *cast_3 = CAST(32, MSB(DUP(op_ADD_1)), op_ADD_1);  │
│         reg_alias PC    │                └───────────────────────────────┘          │ ...                                                           │
│         +               │                                                           └───────────────────────────────────────────────────────────────┘
│         imm	u         │
└─────────────────────────┘
```
