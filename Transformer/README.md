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