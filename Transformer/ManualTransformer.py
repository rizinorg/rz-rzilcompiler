# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer, Token
from Transformer.GlobalVar import GlobalVar
from Transformer.Effect import Effect
from Transformer.Effects.Assignment import Assignment, AssignmentType
from Transformer.Pure import Pure, PureType
from Transformer.Pures.Add import Add


ops = dict()


class ManualTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """

    def fbody(self, items):
        # We are at the top. Generate code.
        print("// READ")
        for op in ops.values():
            if op.type == PureType.GLOBAL or op.type == PureType.LOCAL:
                print(op.code_init_var())
        print('\n// EXEC')
        for op in ops.values():
            if op.type == PureType.EXEC or op.type == PureType.MEM:
                print(op.code_init_var())
        print("\n// WRITE")
        for op in ops.values():
            if isinstance(op, Effect):
                print(op.code_init_var())

    # Returned value replaces node in tree
    # Transformers/Visitors are called bottom up! First leaves then parents
    def reg(self, items):
        items: [Token]
        name = ''.join(items)
        reg_type = items[1].type  # src, dest, both

        if reg_type == "SRC_REG":
            # Should be read before use. Add to read list.
            if name not in ops:
                v = GlobalVar(name, True)
                ops[name] = v
                return v
            return ops[name]
        elif reg_type == "DEST_REG":
            # Dest regs are passed as string to SETG()
            if name not in ops:
                v = GlobalVar(name, True)
                ops[name] = v
                return v
            return ops[name]
        elif reg_type == "SRC_DEST_REG":
            if name not in ops:
                v = GlobalVar(name, True)
                ops[name] = v
                return v
            return ops[name]

    def imm(self, items):
        print(f'imm: {items}')
        return f"{items[0]}{items[1]}"

    def assign(self, items):
        items: Token
        dest = items[0]
        assign_type = AssignmentType.ASGN
        src = items[2]
        name = f'assign{dest.get_name()}{src.get_name()}'
        v = Assignment(name, assign_type, dest, src)
        # ! How to handle effects which do the same? Unique ids for effects and non Vars!
        ops[name] = v
        return v

    def add(self, items):
        a = items[0]
        b = items[1]
        name = f'add{a.get_name()}{b.get_name()}'
        v = Add(name, a, b)
        ops[name] = v
        return v

    def mem_write(self, items):
        print(f'mem_write: {items}')
        return f"{items[0]}{items[1]}"

    def mem_read(self, items):
        print(f'mem_read: {items}')
        return f"{items[0]}{items[1]}"

    def mem_access(self, items):
        print(f'mem_access: {items}')
        return f"{items[0]}"
