
*   Adapt scanner regex/parser grammar to fit the manuals syntax. Not the ISA ones.
*   Map basic operations to function calls of RZIL →Spot the missing ones.
*   Map memory operations to RZIL effects → Spot the missing ones.
*   Choose representation of double/quadruble registers in RZIL. Arrays or Bitvectors? Something else?
    *   Mind prediacte registers which are ANDed if two instructions operate on the same.
*   Solve problem with pseudo functions/macros in behavior (e.g.: `can_handle_trap1_virtinsn`, `fpclassify(Rss)`).
    *   How to find them, how to implement them?
    *   How much can be taken from already existing parser code?


*   Parse txt version of manual and extract behavior
    *   Create Python Instruction Object <> Behavior mapping
    *   Substitute `[!]` and `[.new]` according to actual instruction syntax
        *   e.g.:  `if ([!]Pu) { Rd = Rs[.new] }` becomes `if (Pu) { Rd = Rs.new }`
    *   Spot behavior with missing brackets and ask the user to edit it e.g.: `trap1`.
    *   Add cleaned up behavior to its Instruction Object.

For Next milestone

*   After updating scanner patterns/parser grammar run tests on manual instruction behavior. 
    *   Start writing tests!
*   Implement floating point operations. If not alreadz done bz rizin people. See: [https://github.com/rizinorg/rz-hexagon/issues/12#issuecomment-983447973](https://github.com/rizinorg/rz-hexagon/issues/12#issuecomment-983447973)
    *   FP instruction example: `Pd=dfclass(Rss,#u5)`
*   Think about how rizin has to execute the instructions. How to keep track of Register content (Rs.new registers, Read, Execute, write, jump)
    *   See: `3.3.1 Packet execution semantics` inthe manual
*   Implement missing RZIL functions
*   Fix Grammar and scanner regex for failing tests.
*   Implement macros.
