# Transformer

The transformers generate the RzIL code for a given instruction.
The input is an abstract syntax tree (AST) from the Parser.

The main-transformer initializes sub-transformers (can be found in `Pures` and `Effects`).
Each of those sub-transformers handle RzIL code generation for a specific type of AST node.

Currently the compiler generates a unique varible in C for AST node.
So the result of every effect and pure gets written to its own variable.

There are two tasks our `Pure` and `Effect` sub-transformers need to handle:

1. Generating a unique varible name for the `Pure` or `Effect` in the C code.
2. Generate the RzIL code.

Let's look at those tasks in more detail:

## 1. Generated names in RzIL code.

In the semantic defintions of instructions we usually have names which are variable.

E.g. the variable register `rs` can represent register `r0` to `r31`.
During runtime we need to infer its name.

This is why an Effect or Pure can have different variables in the generated code depending on the context.

### Global Pure Variable Names

Global pures need two variables in the RZIL code.

One variable holds the real name. This is the name it is known in the VM context.
And one variable which holds the _value_ of the global pure.

Let's assume we've got a register `rs` in an ISA instruction.
In the compiled RZIL code we need to init two variables for it:

- `rs`: Holds the value of the Pure. We name it just as it is called in the ISA.
- `rs_assoc`: Associate name of the variable. Variables of name `rs_assoc` hold the name as string of the real variable. `rs`, e.g. "R3", "R31" etc.

Let's say we have the ISA instruction `rs = 0x0`.

In this example `rs` represents the real register `R3` during runtime:

This is how the code looks to determine real name of `rs`.

```c
// rs_assoc holds the real register name "R3"
char *rs_assoc = get_real_reg_name_from_insn(insn, "rs");
// Get value of R3 and store it in `rs`
RzILOpPure *rs = VARG(rs_assoc);
```

### Local Pures and Effects

Those need only a single variable name.
Simply because they have no associated counterpart in the VM (like global variables do).

## 2. Generate RzIL code

Each sub-transformer returns the RzIL code via `il_*` methods.

This is a quick overview what kind of code each method returns.

**Pure/PureExec exclusive**
- `il_read`: RZIL code to read the RZIL variable (e.g. `VARL(<name>)` etc.)
- `il_exec`: RZIL code which does the computation (`ADD(<op1>, <op2>)` etc.)

**Effect exclusive**
- `il_write`: RZIL code to execute the effect and manipulates the CM state (`SETL(<name>, <val>)` etc.).

**Effect and Pures**
- `il_init_var`: Generates a C variable which holds the RZIL operation.
  - `RzILOpPure/RzILOpsEffect <name> = <il_read/il_write/il_exec>`
- `get_name`: Returns the name of the RZIL operation (in the example above, it would be `<name>`).

**NOTE**: `Hybrid.il_init_var()` will always call the `Effect.il_init_var()` method.

### Hybrids

Some C operations can not be mapped directly to an Effect or a Pure.
Because they have characteristics of Effects and Pures (they produce a value and change the state of the VM).

For those cases we have Hybrid sub-transformers.
See the `README` in `Hybrids` for details.
