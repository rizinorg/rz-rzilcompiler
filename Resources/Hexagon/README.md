| File | Source      | Purpose |
|------|-------------|---------|
| `macros.h` | Copied from `qemu/target/hexagon/macros.h` | Macros used to define HVX shortcode instrucions. |
| `macros_mmvec.h` | Copied from `qemu/target/hexagon/mmvec/macros.h` | Macros used to define HVX shortcode instrucions. |
| `shortcode.h` | Copied after building `hexagon-linux-user` from `build/target/hexagon/shortcode_generated.h.inc` | Semantic definitions of all instructions. |
| `macro_patches.h` | hasn-written | Our redefintion of macros with qemu specific code. If you need to replace a certain original macro with a different defintion. Do it here. |
| `combined.h` | Concatination of `macros.h`, `macros_mmvec.h` and `shortcode.h`. | This is given to `pcpp` for macro resolvment. |
| `shortcode_resolved.h` | `shortcode.h` but every macro has been replaced with its content. | Holds all instruction defintions in C. |
