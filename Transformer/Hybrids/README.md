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

And in RZIL:

```c
Pure a1 = ADD(VARL(x), VARL(i)); // x + i
Effect e1 = SEQ(
                SETL(t1, a1),                // t1 = x + i
                SETL(i, ADD(VARL(i), 1))     // i = i + 1
                );
Pure a2 = ADD(a1, VARL(i)); // t1 + i

Effect e2 = SEQ(e1, SETL(z', a2)); // First execute a1, then e1, then a2 and finally set z'
```
