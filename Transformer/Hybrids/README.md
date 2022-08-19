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
t1 = x + i;
i = i + 1
z' = t1 + i
```

Let's draw this out in a graph (read from bottom to top):

```commandline
  ┌─────────────────────────────────┐
  │Effect r2   z' = result          │
  └┬────────────────────────────────┘
   │
   │               result
   │                  │
   │                  │
depends
  on                  +
   │                /   \
   │               /     \
   │            tmp1      i
   │             │
   ▼             │
  ┌──────────────┴──────────────────┐
  │Effect r1   tmp1 = x + i         │
  │            i    = i + 1         │
  └──────────────┬──────────────────┘
                 │
                 │

                 +
                / \
               x   i

         z' = (x + i++) + i
```

And in RZIL:

```c
Pure a1 = ADD(VARL(x), VARL(i)); // x + i
Effect r1 = SEQ(
                SETL(t1, a1),                // t1 = x + i
                SETL(i, ADD(VARL(i), 1))     // i = i + 1
                );
Pure a2 = ADD(a1, VARL(i)); // t1 + i

Effect r2 = SEQ(r1, SETL(z', a2)); // First execute a1, then e1, then a2 and finally set z'
```
Note that the effect `r2` depends on the previous effect `r1` which increments `i` and sets
the `LocalVar(tmp1)`.

So to solve these dependencies during the Transformation we:
- Call a `resolve_hybrids` on each pure returned from a Transformer method. If the pure contains a hybrid
it adds the hybrid effect to a `hybrid-effect-list`, creates the `LocalVar(tmp1)` and returns it.
- Calls `check_hybrid_dependencies` on each effect returned from a Transformer method.
If the original effect has a dependency on a hybrid effect (`len(hybrid-effect-list) != 0`)
it returns `Sequence(r1, r2)` instead of only the original effect.

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
If the function returns a value, it is stored in `LocalVar(tmpX)`.
If it doesn't the local variable is never used and the effect of the hybrid is added when it's compound statement is transformed.
