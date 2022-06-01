# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import re

from lark import Transformer, Token
from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.Pures.BitOp import BitOperationType, BitOp
from Transformer.Pures.Immediate import Immediate
from Transformer.Pures.LetVar import LetVar
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.Number import Number
from Transformer.Pures.Pure import Pure
from Transformer.Effects.Assignment import Assignment, AssignmentType
from Transformer.Pures.ArithmeticOp import ArithmeticOp, ArithmeticType
from Transformer.Pures.Register import Register, RegisterAccessType
from Transformer.helper_hexagon import get_value_type_from_reg_type, get_value_type_by_c_type, \
    get_value_type_by_c_number, get_num_base_by_token, get_value_type_by_isa_imm


class RZILTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """
    op_count = 0

    def get_op_id(self):
        op_id = self.op_count
        self.op_count += 1
        return op_id

    def fbody(self, items):
        holder = ILOpsHolder()
        # We are at the top. Generate code.
        print("// READ")
        for op in holder.read_ops.values():
            print(op.il_init_var())
        print('\n// EXEC')
        for op in holder.exec_ops.values():
            print(op.il_init_var())
        print("\n// WRITE")
        for op in holder.write_ops.values():
            print(op.il_init_var())
        #
        # Wrap into LET(...SEQ(
        #

    # Returned value replaces node in tree
    # Transformers/Visitors are called bottom up! First leaves then parents
    def reg(self, items):
        holder = ILOpsHolder()
        items: [Token]
        name = ''.join(items)
        reg_type = items[1].type  # src, dest, both
        v_type = get_value_type_from_reg_type(items)

        if reg_type == RegisterAccessType.R or reg_type == RegisterAccessType.PR:
            # Should be read before use. Add to read list.
            if name not in holder.read_ops:
                v = Register(name, RegisterAccessType.R, v_type)
                return v
            return holder.read_ops[name]
        elif reg_type == RegisterAccessType.W or reg_type == RegisterAccessType.PW:
            # Dest regs are passed as string to SETG(). Need no Pure variable.
            if name not in holder.read_ops:
                v = Register(name, RegisterAccessType.W, v_type)
                return v
            return holder.read_ops[name]
        elif reg_type == RegisterAccessType.RW or reg_type == RegisterAccessType.PRW:
            if name not in holder.read_ops:
                v = Register(name, RegisterAccessType.RW, v_type)
                return v
            return holder.read_ops[name]

    # SPECIFIC FOR: Hexagon
    def imm(self, items):
        v_type = get_value_type_by_isa_imm(items)
        name = f'{items[0]}'
        return Immediate(name, -1, v_type)

    def number(self, items):
        v_type = get_value_type_by_c_number(items)
        num_str = (str(items[0]) if items[0] else '') + str(items[1])
        name = f'const_{"neg" if items[0] == "-" else "pos"}{items[1]}{items[2] if items[2] else ""}'
        return Number(name, int(num_str, get_num_base_by_token(items[1])), v_type)

    def declaration(self, items):
        if len(items) != 2:
            raise NotImplementedError('')
        t = get_value_type_by_c_type(items[0])
        if isinstance(items[1], Assignment):
            assg: Assignment = items[1]
            assg.dest.set_value_type(t)
        elif isinstance(items[1], str):
            return LocalVar(items[1], get_value_type_by_c_type(items[0]))
        return

    def init_declarator(self, items):
        if len(items) != 2:
            raise NotImplementedError('')
        dest = LocalVar(items[0], None)  # Size is updated in declaration handler.
        op_type = AssignmentType.ASSIGN
        src: Pure = items[1]
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = Assignment(name, op_type, dest, src)
        return v

    def assignment_expr(self, items):
        dest: Pure = items[0]
        op_type = AssignmentType(items[1])
        src: Pure = items[2]
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = Assignment(name, op_type, dest, src)
        return v

    def additive_expr(self, items):
        a = items[0]
        b = items[2]
        op_type = ArithmeticType(items[1])
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = ArithmeticOp(name, a, b, op_type)
        return v

    def and_expr(self, items):
        return self.bit_operations(items, BitOperationType.BIT_AND_OP)

    def inclusive_or_expr(self, items):
        return self.bit_operations(items, BitOperationType.BIT_OR_OP)

    def exclusive_or_expr(self, items):
        return self.bit_operations(items, BitOperationType.BIT_XOR_OP)

    def unary_expr(self, items):
        if items[0] == '~':
            return self.bit_operations(items, BitOperationType.BIT_NOT_OP)
        else:
            raise NotImplementedError('')

    def bit_operations(self, items: list, op_type: BitOperationType):
        if len(items) < 3:
            # Single operand bit operation e.g. ~
            a = items[1]
            name = f'op_{op_type.name}_{self.get_op_id()}'
            v = BitOp(name, a, None, op_type)
            return v
        a = items[0]
        b = items[2]
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = BitOp(name, a, b, op_type)
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
