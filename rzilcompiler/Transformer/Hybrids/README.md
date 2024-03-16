<!--
SPDX-FileCopyrightText: 2023 Rot127

SPDX-License-Identifier: LGPL-3.0-only
-->

Hyprid classes are operations which must inherit from Effect _and_ Pure.

Certain operations in languages we get as input require these.

Think about the unary increment statement in C `i++`. It returns the value `i` and increments it afterwards.
Since this logic is not separated in the syntax we need a class which represents the `++` operation and
emits:
- The Pure `i`
- The increment Effect `i = i + 1`

**Example**

Think about the statement: `z = (x + i) + i`.
Since no `++` operation takes place, it can simply be written as:

```c
Pure a1 = ADD(VARL(x), VARL(i));
Pure a2 = ADD(a1, VARL(i));

Effect e1 = SETL(z, a2);
```

Now let's say our statement looks like this: `z' = (x + i++) + i`.
Here we can't write it as a sequence of Pure operations.
RZIL strictly separates Pures and Effects. So we need to generate RZIL code which does the following:

```c
h_tmp1 = i;
i = i + 1
z' = h_tmp1 + x + i
```

Let's draw this out in a graph (read from bottom to top):

```
  ┌─────────────────────────────────┐
  │Effect r2   z = result           │
  └┬────────────────────┬───────────┘
   │                    │
   │                    │
   │                    │
   │                    │
   │
depends                 +
  on                   / \
   │                  /   \
   │                 /     i
   │                /
   │               +
   │              / \
   │             x  h_tmp1
   │                 │
   │                 │
   ▼                 │
  ┌──────────────────┴──────────────┐
  │Effect r1   h_tmp1 = i           │
  │            i    = i + 1         │
  └──────────────────┬──────────────┘
                     │
                     │
                    ─┴─
          z' = (x + i++) + i
```

And in RZIL:

```c
Effect r1 = SEQ(
                SETL(h_tmp1, VARL(i)),         // h_tmp1 = i
                SETL(i, ADD(VARL(i), 1))       // i = i + 1
                );
Pure a1 = ADD(VARL(x), VARL(h_tmp1));          // (x + h_tmp1)
Pure a2 = ADD(a1, VARL(i));                    // (x + h_tmp1) + i

// First execute r1 to back up originla i value, then a1, a2 and set z' (execute r2)
Effect r2 = SEQ(r1, SETL(z', a2));
```

Note that the effect `r2` depends on the previous effect `r1` which increments `i` and sets
the `LocalVar(h_tmp1)`.

So to solve these dependencies during the Transformation we:

- Call a `resolve_hybrid` on Hybrid which is initialized in a Transformer method.
The hybrid's effect is added to a `hybrid_effect_list` and a `LocalVar(h_tmp1)` is returned for the parent to consume it.
`LocalVar(h_tmp1)` holds the value the parent should consume and is set in the just added effect.

- Call `check_hybrid_dependencies` on each effect returned from a Transformer method.
If the original effect has a dependency on a hybrid effect (`len(hybrid_effect_list) != 0`)
it returns `Sequence(r1, r2)` instead of only the original effect.
Note that this also applies for hybrid effects! This makes semantics like `(i++ + i++)` possible.

### Calls to functions within sematic descriptions

The instruction semantics written in C can make use of function calls.
Modeling this within RZIL is tricky because the branch to an RZIL implementation of this function would be its own operation.

This is why calls are treated as `Hybrids`.

There are three function types:
- Function store something (`Effect`); returns nothing
  - e.g. write `v` to register `X`.
- Function transforms input (`PureExec`); stores nothing; returns value (`Pure`)
  - e.g. extract bit 5-10 from value `v` and return result.
- Function transforms value (`PureExec`); stores something (`Effect`); returns value (`Pure`)
  - e.g. count leading zeros: get number, writes temporary variables and returns zero count.

Luckily all this can be done with the hybrids described above.
The only difference is that your RZIL implementation of the function should store its return value in
an unsigned local variable `ret_val`. This local variable will hold all return values of function call within one IL op.
