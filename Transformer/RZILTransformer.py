# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer

from ArchEnum import ArchEnum
from Transformer.Effects.Jump import Jump
from Transformer.Effects.MemStore import MemStore
from Transformer.HexagonExtension import HexagonExtension
from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.Pures.BitOp import BitOperationType, BitOp
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.MemLoad import MemAccessType, MemLoad
from Transformer.Pures.Number import Number
from Transformer.Pures.Pure import Pure, ValueType
from Transformer.Effects.Assignment import Assignment, AssignmentType
from Transformer.Pures.ArithmeticOp import ArithmeticOp, ArithmeticType
from Transformer.helper_hexagon import get_value_type_by_c_number, get_num_base_by_token, get_c_type_by_value_type


class RZILTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """
    op_count = 0

    def __init__(self, arch: ArchEnum):

        self.arch = arch

        if self.arch == ArchEnum.HEXAGON:
            self.ext = HexagonExtension()
        else:
            raise NotImplementedError(f'Architecture {self.arch} has not Transformer extension.')
        super().__init__()

    def get_op_id(self):
        op_id = self.op_count
        self.op_count += 1
        return op_id

    def fbody(self, items):
        self.ext.set_token_meta_data('fbody')

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

    # SPECIFIC FOR: Hexagon
    def new_reg(self, items):
        self.ext.set_token_meta_data('new_reg')

        return self.ext.hex_reg(items, True)

    def reg(self, items):
        self.ext.set_token_meta_data('reg')

        return self.ext.reg(items)

    def imm(self, items):
        self.ext.set_token_meta_data('imm')

        return self.ext.imm(items)

    def jump(self, items):
        self.ext.set_token_meta_data('jump')
        ta: Pure = items[0]
        return Jump(f'jump_{ta.name}', ta)

    def number(self, items):
        self.ext.set_token_meta_data('number')

        v_type = get_value_type_by_c_number(items)
        num_str = (str(items[0]) if items[0] else '') + str(items[1])
        name = f'const_{"neg" if items[0] == "-" else "pos"}{items[1]}{items[2] if items[2] else ""}'
        return Number(name, int(num_str, get_num_base_by_token(items[1])), v_type)

    def declaration(self, items):
        self.ext.set_token_meta_data('declaration')

        if len(items) != 2:
            raise NotImplementedError(f'Declaration without exactly two tokens are not supported.')
        t = self.ext.get_value_type_by_resource_type(items[0])
        if isinstance(items[1], Assignment):
            assg: Assignment = items[1]
            assg.dest.set_value_type(t)
        elif isinstance(items[1], str):
            return LocalVar(items[1], t)
        return

    def init_declarator(self, items):
        self.ext.set_token_meta_data('init_declarator')

        if len(items) != 2:
            raise NotImplementedError(f'Can not initialize an Init declarator with {len(items)} tokens.')
        dest = LocalVar(items[0], None)  # Size is updated in declaration handler.
        op_type = AssignmentType.ASSIGN
        src: Pure = items[1]
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = Assignment(name, op_type, dest, src)
        return v

    def assignment_expr(self, items):
        self.ext.set_token_meta_data('assignment_expr')

        dest: Pure = items[0]
        op_type = AssignmentType(items[1])
        src: Pure = items[2]
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = Assignment(name, op_type, dest, src)
        return v

    def additive_expr(self, items):
        self.ext.set_token_meta_data('additive_expr')

        a = items[0]
        b = items[2]
        op_type = ArithmeticType(items[1])
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = ArithmeticOp(name, a, b, op_type)
        return v

    def and_expr(self, items):
        self.ext.set_token_meta_data('and_expr')

        return self.bit_operations(items, BitOperationType.BIT_AND_OP)

    def inclusive_or_expr(self, items):
        self.ext.set_token_meta_data('inclusive_or_expr')

        return self.bit_operations(items, BitOperationType.BIT_OR_OP)

    def exclusive_or_expr(self, items):
        self.ext.set_token_meta_data('exclusive_or_expr')

        return self.bit_operations(items, BitOperationType.BIT_XOR_OP)

    def unary_expr(self, items):
        self.ext.set_token_meta_data('unary_expr')

        if items[0] == '~':
            return self.bit_operations(items, BitOperationType.BIT_NOT_OP)
        else:
            raise NotImplementedError(f'Unary expression {items[0]} not handler.')

    def bit_operations(self, items: list, op_type: BitOperationType):
        self.ext.set_token_meta_data('bit_operations')

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
        self.ext.set_token_meta_data('mem_store')
        va = items[2][0]
        data: Pure = items[2][1]
        operation_value_type = ValueType(items[0] != 'u', int(items[1]))
        if not data.value_type == operation_value_type:
            raise ValueError('Mismatch between memory access size and data size.\n'
                             f'data: size: {data.value_type.bit_width} signed: {data.value_type.signed}\n'
                             f'mem op: size: {operation_value_type.bit_width} signed: {operation_value_type.signed}')
        return MemStore(f'ms_{data.get_name()}', va, data)

    # SPECIFIC FOR: Hexagon
    def mem_load(self, items):
        self.ext.set_token_meta_data('mem_load')
        vt = ValueType(items[0] != 'u', int(items[1]))
        vt.c_type = get_c_type_by_value_type(vt)
        mem_acc_type = MemAccessType(vt, True)
        va = items[2]
        if not isinstance(va, Pure):
            va = ILOpsHolder().get_op_by_name(va.value)

        return MemLoad(f'ml_{va.get_name()}', va, mem_acc_type)

    def argument_expr_list(self, items):
        self.ext.set_token_meta_data('argument_expr_list')
        return list(items)
