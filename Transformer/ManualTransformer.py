# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer, Token
from Transformer.GlobalVar import GlobalVar
from Transformer.Effects.Assignment import Assignment, AssignmentType
from Transformer.Pure import Pure

ops = []


class ManualTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """

    def fbody(self, items):
        # We are at the top. Generate code.
        for op in ops:
            print(op.code_init_var())

    # Returned value replaces node in tree
    # Transformers/Visitors are called bottom up! First leaves then parents
    def reg(self, items):
        items: [Token]
        name = ''.join(items)
        reg_type = items[1].type  # src, dest, both

        if reg_type == "SRC_REG":
            # Should be read before use. Add to read list.
            v = GlobalVar(name)
            ops.append(v)
            return v
        elif reg_type == "DEST_REG":
            # Dest regs are passed as string to SETG()
            v = GlobalVar(name)
            ops.append(v)
            return v
        elif reg_type == "SRC_DEST_REG":
            v = GlobalVar(name)
            ops.append(v)
            return v

    def imm(self, items):
        print(f'imm: {items}')
        return f"{items[0]}{items[1]}"

    def assign(self, items):
        items: Token
        dest = items[0]
        assign_type = AssignmentType.ASGN # AssignmentType[items[1].value]
        src = items[2]
        v = Assignment(f'assign{dest.code_get_op_name()}{src.code_get_op_name()}', assign_type, dest, src)
        ops.append(v)
        return v

    def add(self, items):
        print(f'add: {items}')
        return f"{items[0]}{items[1]}"

    def mem_write(self, items):
        print(f'mem_write: {items}')
        return f"{items[0]}{items[1]}"

    def mem_read(self, items):
        print(f'mem_read: {items}')
        return f"{items[0]}{items[1]}"

    def mem_access(self, items):
        print(f'mem_access: {items}')
        return f"{items[0]}"
