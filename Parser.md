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
