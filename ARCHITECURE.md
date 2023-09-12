<!--
SPDX-FileCopyrightText: 2023 Rot127

SPDX-License-Identifier: LGPL-3.0-only
-->

The overall structure of the compiler consists of:

1. The **Preprocessor** which formats the input data before it is given to the **Parser**.
1. The **Parser** and a grammar. The parser used here is the [Lark](https://github.com/lark-parser/lark) compiler and a modified version of the C grammar.
1. The **Transformer**. The Transformer module generates the actual code from the parsing tree.
1. The **Post-Processor**. There is no Post-Processor in this repository. For the Hexagon architecture [rz-hexagon](https://github.com/rizinorg/rz-hexagon/) does the post-processing.

Here is the overview how the components are chained together.

```
                                                              ┌──────────┐       ┌──────────┐      ┌──────────┐                      ┌──────────┐       ┌──────────┐      ┌──────────┐
                                                              │ Hexagon  │       │ <Arch-B> │      │ <Arch-C> │                      │ Hexagon  │       │ <Arch-B> │      │ <Arch-C> │
                                                              │   (C)    │       │          │      │          │                      │          │       │          │      │          │
                                                              │ Grammar  │       │ Grammar  │      │ Grammar  │                      │ Special  │       │ Special  │      │ Special  │
                                                              │          │       │          │      │          │                      │ Tokens   │       │ Tokens   │      │ Tokens   │
                                                              └─────┬────┘       └─────┬────┘      └─────┬────┘                      └─────┬────┘       └─────┬────┘      └─────┬────┘
                                                                    │                  │                 │                                 │                  │                 │
                                                                    │                  │                 │                                 │                  │                 │
                                                                    │                  │                 │                                 │                  │                 │
                                                                    │                  │                 │                                 │                  │                 │
                                                                    │                  │                 │                                 │                  │                 │
                                                                    └──────────────────┼─────────────────┘                                 └──────────────────┼─────────────────┘
                                                                                       │                                                                      │
                                                                                       │                                                                      │
                                                                                       │                                                                      │
                                                                                       │                                                                      │
    ┌────────────┐            ┌────────────┐                                           │                                                                      │
    │  Hexagon   │            │ Hexagon    │                                           │                                                                      │
    │            ├───────────►│ Post-      ├───────────────┐                           │                                                                      │
    │ Resources  │            │ Processor  │               │                           │                                                                      │
    └────────────┘            └────────────┘               │                           │                                                                      │
                                                           │                           │                                                                      │
                                                           │                           ▼                                                                      ▼
                                                           │               ┌───────────────────────┐                                              ┌───────────────────────┐                               ┌───────────────────────┐
                                                           │               │                       │                                              │                       │                               │                       │
    ┌────────────┐            ┌────────────┐               │               │                       │                                              │                       │                               │                       │
    │  <Arch-B>  │            │ <Arch-B>   │               │               │                       │                                              │                       │                               │                       │
    │            ├───────────►│ Post-      ├───────────────┼──────────────►│    Parser (Lark)      ├─────────────────────────────────────────────►│   Transformer         ├──────────────────────────────►│   Post-Procesor       │
    │ Resources  │            │ Processor  │               │               │                       │                                              │                       │                               │                       │
    └────────────┘            └────────────┘               │               │                       │                                              │                       │                               │                       │
                                                           │               │                       │                                              │                       │                               │                       │
                                                           │               │                       │                                              │                       │                               │                       │
                                                           │               └───────────────────────┘                                              └───────────────────────┘                               └───────────────────────┘
                                                           │
    ┌────────────┐            ┌────────────┐               │
    │  <Arch-C>  │            │ <Arch-C>   │               │
    │            ├───────────►│ Post-      ├───────────────┘
    │ Resources  │            │ Processor  │
    └────────────┘            └────────────┘
```

To get an idea what each step does with the input, lets follow an example about an Hexagon instruction.

`{ RdV=fREAD_PC()+fIMMEXT(uiV);}` is the semantic of an Hexagon instruction (in C with macros). It is given to the Pre-Processor.

The Pre-Processor resolves the macros in the C code and passes the result on to the Parser.

```
                 { RdV=fREAD_PC()+fIMMEXT(uiV);}
                ────────────────┬────────────────
                                │
                                │
                                │
┌─────────────────────┐         │         ┌────────────────────┐
│                     │         │         │                    │
│  Hexagon            │         │         │   Pre-             │
│                     │         │         │   Processor        │
│  Resource           ├─────────┴────────►│                    ├────────────────►   { RdV=(HEX_REG_ALIAS_PC)+(uiV);}
│                     │                   │                    │
│                     │                   │                    │
└─────────────────────┘                   └────────────────────┘
```

The Parser builds the parse tree with the help of our modified C grammar. The parse tree is given to the Transformer.

```
                                   ┌─────────────────────────────────────────────────────────────────┐
                                   │...                                                              │
                                   │_reg_variant: "HEX_REG_ALIAS_" reg_alias                         │
                                   │    | new_reg "N"                                                │
                                   │    | reg "V"                                                    │
                                   │    | explicit_reg                                               │
                                   │                                                                 │
                                   │!explicit_reg: ("R31" | "P0" | "P1" | "P2" | "P3") ["_NEW"]      │
                                   │                                                                 │
                                   │new_reg: _reg                                                    │
                                   │reg: _reg                                                        │
                                   │                                                                 │
                                   │                                                                 │
                                   │                                                                 │
                                   │...                                                              │
                                   └─────────────────────────┬───────────────────────────────────────┘
                                                             │
                                                             │ Grammar
                                                             │
                                                             ▼
                                                  ┌─────────────────────┐                       ┌─────────────────────────┐
                                                  │                     │                       │ fbody                   │
                                                  │                     │                       │   block_item            │
                                                  │                     │     Parse tree        │     assignment_expr     │
{ RdV=(HEX_REG_ALIAS_PC)+(uiV);} ────────────────►│  Parser (Lark)      ├──────────────────────►│       reg               │
                                                  │                     │                       │         R               │
                                                  │                     │                       │         d               │
                                                  │                     │                       │       =                 │
                                                  └─────────────────────┘                       │       additive_expr     │
                                                                                                │         reg_alias PC    │
                                                                                                │         +               │
                                                                                                │         imm	u         │
                                                                                                └─────────────────────────┘
```

The Transformer generates the equivalent `RZIL` code for each tree node.
Special cases which are not generalizable between Architectures can be handled in Extensions.

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

The resulting `RZIL` code is then passed to the Post-Processor or simply printed to `stdout`.
