# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer, Token
from Transformer.GlobalVar import GlobalVar
from Transformer.Effect import Effect
from Transformer.Effects.Assignment import Assignment, AssignmentType
from Transformer.Pure import Pure, PureType
from Transformer.Pures.Add import Add
from Transformer.Register import Register, RegisterAccessType


ops = dict()


class RZILTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """

    def fbody(self, items):
        # We are at the top. Generate code.
        print("// READ")
        for op in ops.values():
            if isinstance(op, Register):
                print(op.il_init_var())
        print('\n// EXEC')
        for op in ops.values():
            if op.type == PureType.EXEC:
                print(op.il_init_var())
        print("\n// WRITE")
        for op in ops.values():
            if isinstance(op, Effect):
                print(op.il_init_var())

    # Returned value replaces node in tree
    # Transformers/Visitors are called bottom up! First leaves then parents
    def reg(self, items):
        print(items)
        items: [Token]
        name = ''.join(items)
        reg_type = items[1].type  # src, dest, both

        if reg_type == RegisterAccessType.R or reg_type == RegisterAccessType.PR:
            # Should be read before use. Add to read list.
            if name not in ops:
                v = Register(name, RegisterAccessType.R, -1)
                ops[name] = v
                return v
            return ops[name]
        elif reg_type == RegisterAccessType.W or reg_type == RegisterAccessType.PW:
            # Dest regs are passed as string to SETG(). Need no Pure variable.
            if name not in ops:
                v = Register(name, RegisterAccessType.W, -1)
                ops[name] = v
                return v
            return ops[name]
        elif reg_type == RegisterAccessType.RW or reg_type == RegisterAccessType.PRW:
            if name not in ops:
                v = Register(name, RegisterAccessType.RW, -1)
                ops[name] = v
                return v
            return ops[name]

    def imm(self, items):
        print(f'imm: {items}')
        return f"{items[0]}{items[1]}"

    def assignment_expr(self, items):
        print(items)
        dest: Pure = items[0]
        assign_type = AssignmentType(items[1])
        src: Pure = items[2]
        name = f'assign{dest.get_isa_name()}{src.get_isa_name()}'
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
