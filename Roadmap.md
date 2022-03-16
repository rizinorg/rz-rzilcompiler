
## Block I

- [x]   Adapt scanner regex/parser grammar to fit the manuals syntax. Not the ISA ones.
- [x]   Map basic operations to function calls of RZIL → Spot the missing ones.
- [x]   Map memory operations to RZIL effects → Spot the missing ones.
- [x]   Choose representation of double/quadruble registers in RZIL. -> See: _Can't find the link. But registers can be devided and addressed within BAP._
  - [x]   Mind prediacte registers which are ANDed if two instructions operate on the same.  -> Implement function for that.
- [x]   Solve problem with pseudo functions/macros in behavior (e.g.: `can_handle_trap1_virtinsn`, `fpclassify(Rss)`). -> Some are defined in the QEMU `macros.h` file. Some not. Those need to be implementd, or we ignore them.
  - [x]   How to find them, how to implement them?
  - [x]   How much can be taken from already existing parser code? -> Macros.

- [ ]   Parse txt version of manual and extract behavior
  - [x]   Extract behavior and syntax from txt manual.
  - [ ]   Create Python Instruction Object <> Behavior mapping
  - [ ]   Substitute `[!]` and `[.new]` according to actual instruction syntax
    - [ ]   e.g.:  `if ([!]Pu) { Rd = Rs[.new] }` becomes `if (Pu) { Rd = Rs.new }`
  - [ ]   Spot behavior with missing brackets and ask the user to edit it e.g.: `trap1`.
  - [ ]   Add cleaned up behavior to its Instruction Object.

## Block II

- [ ] Finish Block I tasks.
- [ ] Test extracted bahvior against parser grammar and correct results.
  - [ ] Correct result of preprocessor.
  - [ ] Correct grammar
    - [ ] Resolve ambiquities.
    - [ ] Add missin grammar.
- [ ] Document all macros which need replacement.
  - [ ] Match against existing macros in QEMUs `macros.h`
- [x] Implement missing RZIL effects etc.
  - No missing effects seen yet.
- [ ] Implement most common missing macros.
- [ ] How to handle `assembler maps to?`
- [x] Implement floating point operations. If not already done by rizin people. See: [https://github.com/rizinorg/rz-hexagon/issues/12#issuecomment-983447973](https://github.com/rizinorg/rz-hexagon/issues/12#issuecomment-983447973)
  - @heersin finishes it. In case she/he isn't done when we need it, we can help. [Branch](https://github.com/Heersin/rizin/commits/rz_util_float)

## Block III

- [ ] Think about how rizin has to execute the instructions. How to keep track of Register content (Rs.new registers, Read, Execute, write, jump)
    *  See: `3.3.1 Packet execution semantics` inthe manual

## Test ideas

- AES
- Compression
- CrackMe binaries
