# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer, Token

from Transformer.Effects.MemStore import MemStore
from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.Pures.BitOp import BitOperationType, BitOp
from Transformer.Pures.Immediate import Immediate
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.MemLoad import MemAccessType, MemLoad
from Transformer.Pures.Number import Number
from Transformer.Pures.Pure import Pure, ValueType
from Transformer.Effects.Assignment import Assignment, AssignmentType
from Transformer.Pures.ArithmeticOp import ArithmeticOp, ArithmeticType
from Transformer.Pures.Register import Register, RegisterAccessType
from Transformer.helper_hexagon import get_value_type_from_reg_type, get_value_type_by_c_type, \
    get_value_type_by_c_number, get_num_base_by_token, get_value_type_by_isa_imm, get_c_type_by_value_type


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
        res = ''
        # We are at the top. Generate code.
        res += "// READ\n"
        for op in holder.read_ops.values():
            res += op.il_init_var() + '\n'
        res = '\n// EXEC\n'
        for op in holder.exec_ops.values():
            res += op.il_init_var() + '\n'
        res += "\n// WRITE\n"
        for op in holder.write_ops.values():
            res += op.il_init_var() + '\n'
        return res

    def new_reg(self, items):
        return self.hex_reg(items, True)

    def reg(self, items):
        return self.hex_reg(items, False)

    def hex_reg(self, items, is_new: bool):
        holder = ILOpsHolder()
        items: [Token]
        name = ''.join(items)
        reg_type = items[1].type  # src, dest, both
        v_type = get_value_type_from_reg_type(items)

        if reg_type == RegisterAccessType.R or reg_type == RegisterAccessType.PR:
            # Should be read before use. Add to read list.
            if name in holder.read_ops:
                return holder.read_ops[name]
            v = Register(name, RegisterAccessType.R, v_type, is_new)
        elif reg_type == RegisterAccessType.W or reg_type == RegisterAccessType.PW:
            # Dest regs are passed as string to SETG(). Need no Pure variable.
            if name in holder.read_ops:
                return holder.read_ops[name]
            v = Register(name, RegisterAccessType.W, v_type, is_new)
        elif reg_type == RegisterAccessType.RW or reg_type == RegisterAccessType.PRW:
            if name in holder.read_ops:
                return holder.read_ops[name]
            v = Register(name, RegisterAccessType.RW, v_type, is_new)
        else:
            raise NotImplementedError(f'Reg type "{reg_type.name}" not implemented.')
        v.set_isa_name(name)
        return v

    # SPECIFIC FOR: Hexagon
    def imm(self, items):
        v_type = get_value_type_by_isa_imm(items)
        name = f'{items[0]}'
        imm = Immediate(name, -1, v_type)
        imm.set_isa_name(name)
        return imm

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

    def mem_store(self, items):
        va = items[2][0]
        data: Pure = items[2][1]
        print(va, data)
        operation_value_type = ValueType('', items[0] != 'u', int(items[1]))
        if not data.value_type == operation_value_type:
            raise ValueError('Mismatch between memory access size and data size.\n'
                             f'data: size: {data.value_type.bit_width} signed: {data.value_type.signed}\n'
                             f'mem op: size: {operation_value_type.bit_width} signed: {operation_value_type.signed}')
        return MemStore(f'ms_{data.get_name()}', va, data)

    # SPECIFIC FOR: Hexagon
    def mem_load(self, items):
        vt = ValueType('unknown_t', items[0] != 'u', int(items[1]))
        vt.c_type = get_c_type_by_value_type(vt)
        mem_acc_type = MemAccessType(vt, True)
        va = items[2]
        if not isinstance(va, Pure):
            va = ILOpsHolder().get_op_by_name(va.value)

        return MemLoad(f'ml_{va.get_name()}', va, mem_acc_type)

    def argument_expr_list(self, items):
        return list(items)

