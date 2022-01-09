All unsigned operations have also a signed variant.

|-------------|----------------|
| C Operation | RZIL Operation |
|-------------|----------------|
| +           | rz_il_op_new_add |
| -           | rz_il_op_new_sub |
| *           | rz_il_op_new_mul |
| /           | rz_il_op_new_div |
| %           | rz_il_op_new_mod |
| **          | - |
| <           | Mapped (leq) |
| >           | Mapped |
| ^           | rz_il_op_new_bool_xor |
| |           | rz_il_op_new_log_or |
| &           | rz_il_op_new_log_and |
| >>          | rz_il_op_new_shiftr |
| <<          | rz_il_op_new_shiftl |
| ++          | Mapped |
| --          | Mapped |
| ->          | - |
| &&          | rz_il_op_new_bool_and |
| ||          | rz_il_op_new_bool_or  |
| ^ (bool)    | rz_il_op_new_bool_xor |
| unary -     | rz_il_op_new_neg |
| unary !     | rz_il_op_new_bool_inv |
| unary +     | Needed? |
| unary *     | - |
| unary ~     | - |
| >>=         | - |
| <<=         | - |
| =           | rz_il_op_new_store |
| +=          | Mapped |
| -=          | Mapped |
| *=          | Mapped |
| /=          | Mapped |
| %=          | Mapped |
| &=          | Mapped |
| ^=          | Mapped |
| |=          | Mapped |
| >=          | Mapped |
| !=          | Mapped |
| <=          | rz_il_op_new_ule |
| ==          | rz_il_op_new_eq |
| for         | rz_il_op_new_repeat |
| while       | rz_il_op_new_repeat |
| []          | rz_il_op_new_load |
| .           | - |
| branching   | rz_il_op_new_branch |
| casts       | rz_il_op_new_cast, ... |
| NOP         | rz_il_op_new_nop |
| jump        | rz_il_op_new_jmp |
| goto        | rz_il_op_new_goto |

- `LOAD` and `LOAD_WORD` are already implemented. `LOAD_DWORD`, `LOAD_QWORD` and the like would be useful as well.


