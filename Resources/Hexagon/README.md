<!--
SPDX-FileCopyrightText: 2023 Rot127

SPDX-License-Identifier: LGPL-3.0-only
-->

| File                   | Source                                                                                           | Purpose                                                                                                                                    |
|------------------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `macros.h`             | Copied from `qemu/target/hexagon/macros.h`                                                       | Macros used to in shortcode definitions                                                                                                    |
| `macros_mmvec.h`       | Copied from `qemu/target/hexagon/mmvec/macros.h`                                                 | Macros used to define HVX shortcode instructions.                                                                                           |
| `macros.inc`           | Copied from `qemu/target/hexagon/idef-parser/macros.inc`                                         | Macros used to ease parsing                                                                                                                |                                                                                                               |
| `patches_macro.h`      | hand-written                                                                                     | Our redefinition of macros with qemu specific code. If you need to replace a certain original macro with a different defintion. Do it here. |
| `macros_patched.h`     | Concatination of `macros.h`, `macros.inc` and `macros_mmvec.h` with patches.                      |                                                                                                                                            |
| `combined.h`           | Concatination of `macros_patched.h` and `shortcode.h`.                                           | This is given to `pcpp` for macro resolvment.                                                                                              |
| `shortcode.h`          | Copied after building `hexagon-linux-user` from `build/target/hexagon/shortcode_generated.h.inc` | Semantic definitions of all instructions.                                                                                                  |
| `shortcode_resolved.h` | `shortcode.h` but every macro has been replaced with its content.                                | Holds all instruction defintions in C.                                                                                                     |
