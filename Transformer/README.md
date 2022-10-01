Each Effect or Pure can have different names depending on the context.

#### Global Pure Variable Names

Global pures need two variable name in the RZIL code.
One which holds the real name this variable represents.
And one which holds the value of the global pure.

Let's assume we've got a register `rs` in an ISA instruction. In the compiled RZIL code we need to init two variables for it:

- `rs`: ISA name. This is how the variable is written in the ISA definition.
- `rs_assoc`: Associate name. Variables of name `rs_assoc` hold the name as string of the real variable represented by `rs`, e.g. "R3", "R31" etc.

Let's say we have the ISA instruction `rs = 0x0`.
In this example `rs` represents the real register `R3`:
This is how we generate the Pure initialization.
```c
// rs represents the real register R3
char *rs_assoc = get_real_reg_name_from_insn(insn, "rs");
// rs_assoc = "R3"
// Get value of R3 and store it in `rs`
RzILOpPure *rs = VARG(rs_assoc);
```

#### Local Pures and Effects

Those need only a single variable.

# Method description

The `il_` methods return the compiled C code.
This is a quick overview what kind of code each method returns.

**Pure/PureExec exclusive**
- `il_read`: RZIL code to read the RZIL variable (`VARL(<name>)` etc.)
- `il_exec`: RZIL code which does the computation (`ADD(<op1>, <op2>)` etc.)

**Effect exclusive**
- `il_write`: RZIL code to execute the effect (`SETL(<name>, <val>)` etc.).

**Effect and Pures**
- `il_init_var`: Generates a C variable which holds the RZIL ops.
  - `RzILOpPure/RzILOpsEffect <name> = <il_read/il_write/il_exec>`
- `get_name`: Returns the name of the RZIL op.

**NOTE**: `Hybrid.il_init_var()` will always call the `Effect.il_init_var()` method.
