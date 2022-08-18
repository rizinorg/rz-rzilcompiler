# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer, Token

from ArchEnum import ArchEnum
from Transformer.Effects.Branch import Branch
from Transformer.Effects.Effect import Effect
from Transformer.Effects.Empty import Empty
from Transformer.Effects.ForLoop import ForLoop
from Transformer.Effects.Jump import Jump
from Transformer.Effects.MemStore import MemStore
from Transformer.Effects.NOP import NOP
from Transformer.Effects.PredicateWrite import PredicateWrite
from Transformer.Effects.Sequence import Sequence
from HexagonExtensions import HexagonTransformerExtension
from Transformer.Hybrids.Hybrid import Hybrid, PostfixExpr
from Transformer.Hybrids.PostfixIncDec import PostfixIncDec
from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.Pures.BitOp import BitOperationType, BitOp
from Transformer.Pures.BooleanOp import BooleanOpType, BooleanOp
from Transformer.Pures.CCode import CCall
from Transformer.Pures.Cast import Cast
from Transformer.Pures.CompareOp import CompareOp, CompareOpType
from Transformer.Pures.LocalVar import LocalVar
from Transformer.Pures.MemLoad import MemAccessType, MemLoad
from Transformer.Pures.Number import Number
from Transformer.Pures.Pure import Pure, ValueType, PureType
from Transformer.Effects.Assignment import Assignment, AssignmentType
from Transformer.Pures.ArithmeticOp import ArithmeticOp, ArithmeticType
from Transformer.Pures.PureExec import PureExec
from Transformer.Pures.Register import Register
from Transformer.Pures.Ternary import Ternary
from Transformer.Pures.Variable import Variable
from Transformer.helper import exc_if_types_not_match, flatten_list
from Transformer.helper_hexagon import get_value_type_by_c_number, get_num_base_by_token


class RZILTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """
    op_count = 0
    hybrid_op_count = 0

    def __init__(self, arch: ArchEnum):

        self.arch = arch
        self.gcc_ext_effects = list()

        if self.arch == ArchEnum.HEXAGON:
            self.ext = HexagonTransformerExtension()
        else:
            raise NotImplementedError(f'Architecture {self.arch} has not Transformer extension.')
        super().__init__()

    def reset(self):
        self.op_count = 0
        self.ext.reset_flags()
        self.gcc_ext_effects.clear()

    def get_op_id(self):
        op_id = self.op_count
        self.op_count += 1
        return op_id

    def fbody(self, items):
        self.ext.set_token_meta_data('fbody')

        holder = ILOpsHolder()
        res = ''
        # We are at the top. Generate code.
        res += "\n// READ\n"
        for op in holder.read_ops.values():
            res += op.il_init_var() + '\n'

        res += '\n// EXEC\n'
        for op in holder.exec_ops.values():
            if isinstance(op, Hybrid):
                continue
            res += op.il_init_var() + '\n'

        res += "\n// WRITE\n"
        for op in holder.write_ops.values():
            if isinstance(op, Hybrid):
                res += op.il_init_var() + '\n'
                continue
            res += op.il_init_var() + '\n'
        instruction_sequence = Sequence(f'instruction_sequence', [op for op in flatten_list(items) + self.gcc_ext_effects if isinstance(op, Effect)])
        res += instruction_sequence.il_init_var() + '\n'
        res += f'\nreturn {instruction_sequence.effect_var()};'
        return res

    def relational_expr(self, items):
        self.ext.set_token_meta_data('relational_expr')
        return self.compare_op(items)

    def equality_expr(self, items):
        self.ext.set_token_meta_data('equality_expr')
        return self.compare_op(items)

    def reg_alias(self, items):
        self.ext.set_token_meta_data('reg')

        return self.ext.reg_alias(items)

    # SPECIFIC FOR: Hexagon
    def new_reg(self, items):
        self.ext.set_token_meta_data('new_reg')

        return self.ext.hex_reg(items, True)

    def explicit_reg(self, items):
        name = items[0]
        new = items[1] is not None
        self.ext.set_token_meta_data('explicit_reg', is_new=new)
        if name == 'R31':
            # We don't know whether R31 is used as dest or src. Hence: SRC_DEST_REG.
            return self.ext.hex_reg([Token('REG_TYPE', 'R'), Token('SRC_DEST_REG', '31'), name], is_new=new, is_explicit=True)
        elif name[0] == 'P':
            return self.ext.hex_reg([Token('REG_TYPE', 'P'), Token('SRC_DEST_REG', str(name[1])), name], is_new=new, is_explicit=True)
        else:
            raise NotImplementedError(f'Explicit register {items} not handled.')

    def reg(self, items):
        self.ext.set_token_meta_data('reg')

        return self.ext.reg(items)

    def imm(self, items):
        self.ext.set_token_meta_data('imm')

        return self.ext.imm(items)

    def jump(self, items):
        self.ext.set_token_meta_data('jump')
        ta: Pure = items[1]
        return Jump(f'jump_{ta.pure_var()}', ta)

    def data_type(self, items):
        self.ext.set_token_meta_data('data_type')
        return self.ext.get_value_type_by_resource_type(items)

    def cast_expr(self, items):
        self.ext.set_token_meta_data('cast_expr')
        val_type = items[0]
        data = items[1]
        return self.resolve_hybrid_ops(Cast(f'cast_{val_type}_{self.get_op_id()}', val_type, data))

    def number(self, items):
        # Numbers of the form -10ULL
        self.ext.set_token_meta_data('number')

        v_type = get_value_type_by_c_number(items)
        num_str = (str(items[0]) if items[0] else '') + str(items[1])
        name = f'const_{"neg" if items[0] == "-" else "pos"}{items[1]}{items[2] if items[2] else ""}'
        return Number(name, int(num_str, get_num_base_by_token(items[1])), v_type)

    def declaration_specifiers(self, items):
        self.ext.set_token_meta_data('declaration_specifiers')
        specifier: str = items[0]
        t: ValueType = items[1]
        if specifier == 'const':
            # Currently ignore that the variable should be constant.
            return t
        raise NotImplementedError(f'Type specifier {specifier} currently not supported.')

    def declaration(self, items):
        self.ext.set_token_meta_data('declaration')

        if len(items) != 2:
            raise NotImplementedError(f'Declarations without exactly two tokens are not supported.')
        if hasattr(items[0], 'type') and items[0].type != 'IDENTIFIER':
            # Declarations like: "TYPE <id>;" are ignored. They get initialize when they first get set.
            return Empty(f'empty_{self.get_op_id()}')
        t: ValueType = items[0]
        if isinstance(items[1], Assignment):
            assg: Assignment = items[1]
            assg.set_dest_type(t)
            return assg
        elif isinstance(items[1], str):
            return Variable(items[1], t)
        raise NotImplementedError(f'Declaration with items {items} not implemented.')

    def init_declarator(self, items):
        self.ext.set_token_meta_data('init_declarator')

        if len(items) != 2:
            raise NotImplementedError(f'Can not initialize an Init declarator with {len(items)} tokens.')
        dest = Variable(items[0], None)  # Size is updated in declaration handler.
        op_type = AssignmentType.ASSIGN
        src: Pure = items[1]
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = Assignment(name, op_type, dest, src)
        return v

    def selection_stmt(self, items):
        self.ext.set_token_meta_data('selection_stmt')
        cond = items[1]
        then_seq = Sequence(f'seq_then_{self.get_op_id()}', flatten_list(items[2]))
        name = f'branch_{self.get_op_id()}'
        if items[0] == 'if' and len(items) == 3:
            return Branch(name, cond, then_seq, Empty(f'empty_{self.get_op_id()}'))
        elif items[0] == 'if' and len(items) > 3 and items[3] == 'else':
            else_seq = Sequence(f'seq_else_{self.get_op_id()}', flatten_list(items[4]))
            return Branch(name, cond, then_seq, else_seq)
        else:
            raise NotImplementedError(f'"{items[0]}" branch not implemented.')

    def conditional_expr(self, items):
        self.ext.set_token_meta_data('conditional_expr')
        return self.resolve_hybrid_ops(Ternary(f'cond_{self.get_op_id()}', items[0], items[1], items[2]))

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
        return self.resolve_hybrid_ops(v)

    def multiplicative_expr(self, items):
        self.ext.set_token_meta_data('additive_expr')

        a = items[0]
        b = items[2]
        op_type = ArithmeticType(items[1])
        name = f'op_{op_type.name}_{self.get_op_id()}'
        v = ArithmeticOp(name, a, b, op_type)
        return self.resolve_hybrid_ops(v)

    def and_expr(self, items):
        self.ext.set_token_meta_data('and_expr')

        return self.resolve_hybrid_ops(self.bit_operations(items, BitOperationType.AND))

    def inclusive_or_expr(self, items):
        self.ext.set_token_meta_data('inclusive_or_expr')

        return self.resolve_hybrid_ops(self.bit_operations(items, BitOperationType.OR))

    def exclusive_or_expr(self, items):
        self.ext.set_token_meta_data('exclusive_or_expr')

        return self.resolve_hybrid_ops(self.bit_operations(items, BitOperationType.XOR))

    def logical_and_expr(self, items):
        self.ext.set_token_meta_data('logical_and_expr')
        return self.resolve_hybrid_ops(self.boolean_expr(items))

    def logical_or_expr(self, items):
        self.ext.set_token_meta_data('logical_or_expr')
        return self.resolve_hybrid_ops(self.boolean_expr(items))

    def logical_not_expr(self, items):
        self.ext.set_token_meta_data('logical_not_expr')
        return self.resolve_hybrid_ops(self.boolean_expr(items))

    def boolean_expr(self, items):
        a = items[0]
        t = BooleanOpType(items[1])
        b = items[2] if len(items) == 3 else None
        name = f'op_{t}_{self.get_op_id()}'
        v = BooleanOp(name, a, b, t)
        return self.resolve_hybrid_ops(v)

    def shift_expr(self, items):
        self.ext.set_token_meta_data('shift_expr')
        return self.resolve_hybrid_ops(self.bit_operations(items, BitOperationType(items[1])))

    def unary_expr(self, items):
        self.ext.set_token_meta_data('unary_expr')

        if items[0] == '~':
            v = self.bit_operations(items, BitOperationType.NOT)
        elif items[0] == '-':
            v = self.bit_operations(items, BitOperationType.NEG)
        else:
            raise NotImplementedError(f'Unary expression {items[0]} not handler.')
        return self.resolve_hybrid_ops(v)

    def pred_write(self, items):
        pred_reg: Register = items[1]
        self.ext.set_token_meta_data('pred_write', pred_num=pred_reg.get_pred_num())
        name = f'op_PRED_WRITE_{self.get_op_id()}'
        return PredicateWrite(name, items[1], items[2])

    def postfix_expr(self, items):
        self.ext.set_token_meta_data('postfix_expr')
        t = PostfixExpr(items[1])
        name = f'op_{PostfixExpr(items[1]).name}_{self.get_op_id()}'
        if t == PostfixExpr.INC or t == PostfixExpr.DEC:
            op: LocalVar = items[0]
            return PostfixIncDec(name, op, op.value_type, t)
        else:
            raise NotImplementedError(f'Postfix expression {t} not handled.')

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
        return self.resolve_hybrid_ops(v)

    def mem_store(self, items):
        self.ext.set_token_meta_data('mem_store')
        va = items[3]
        data: Pure = items[4]
        operation_value_type = ValueType(items[1] != 'u', int(items[2]))
        if operation_value_type != data.value_type:
            # STOREW determines from the data type how many bytes are written.
            # Cast the data type to the mem store type
            data = Cast(f'op_{self.get_op_id()}', operation_value_type, va)
        return MemStore(f'ms_{data.get_name()}_{self.get_op_id()}', va, data)

    # SPECIFIC FOR: Hexagon
    def mem_load(self, items):
        self.ext.set_token_meta_data('mem_load')
        vt = ValueType(items[1] != 'u', int(items[2]))
        mem_acc_type = MemAccessType(vt, True)
        va = items[3]
        if not isinstance(va, Pure):
            va = ILOpsHolder().get_op_by_name(va.value)

        return self.resolve_hybrid_ops(MemLoad(f'ml_{va.get_name()}_{self.get_op_id()}', va, mem_acc_type))

    def c_call(self, items):
        self.ext.set_token_meta_data('c_call')
        prefix = items[0]
        val_type = self.ext.get_val_type_by_fcn(prefix)
        return CCall(f'c_call_{self.get_op_id()}', val_type, items)

    def identifier(self, items):
        self.ext.set_token_meta_data('identifier')
        # Hexagon shortcode can initialize certain variables without type.
        # Those are converted to a local var here.
        identifier = items[0].value
        holder = ILOpsHolder()
        if identifier in holder.read_ops:
            return holder.read_ops[identifier]
        if self.ext.is_special_id(identifier):
            return self.ext.special_identifier_to_local_var(identifier)
        # Return string. It could be a variable or a function call.
        return identifier

    def compare_op(self, items):
        self.ext.set_token_meta_data('compare_op')
        op_type = CompareOpType(items[1])
        return self.resolve_hybrid_ops(CompareOp(f'op_{op_type.name}_{self.get_op_id()}', items[0], items[2], op_type))

    def for_loop(self, items):
        self.ext.set_token_meta_data('for_loop')
        if len(items) != 5:
            raise NotImplementedError(f'For loops with {len(items)} elements is not supported yet.')
        compound = Sequence(f'seq_{self.get_op_id()}', flatten_list(items[4]) + [items[3]])
        return ForLoop(f'for_{self.get_op_id()}', items[1], items[2], compound)

    def iteration_stmt(self, items):
        self.ext.set_token_meta_data('iteration_stmt')
        if items[0] == 'for':
            return self.for_loop(items)
        else:
            raise NotImplementedError(f'{items[0]} loop not supported.')

    def compound_stmt(self, items):
        self.ext.set_token_meta_data('compound_stmt')
        # These are empty compound statements.
        return Empty(f'empty_{self.get_op_id()}')

    def gcc_extended_expr(self, items):
        self.ext.set_token_meta_data('gcc_extended_expr')
        if isinstance(items[0], list):
            raise NotImplementedError('List of statements in gcc extended expressions not implemented.')
        self.gcc_ext_effects.append(items[0])
        expr = items[1]
        if expr:
            return expr
        raise NotImplementedError('GCC extended expressions without expression are not implemented.')

    def expr_stmt(self, items):
        self.ext.set_token_meta_data('expr_stmt')
        # These are empty expression statements.
        return Empty(f'empty_{self.get_op_id()}')

    def cancel_slot_stmt(self, items):
        self.ext.set_token_meta_data('cancel_slot_stmt')
        return NOP(f'nop_{self.get_op_id()}')

    def block_item_list(self, items):
        self.ext.set_token_meta_data('block_item_list')
        return items

    def block_item(self, items):
        self.ext.set_token_meta_data('block_item')
        return items[0]

    def resolve_hybrid_ops(self, operation: PureExec):
        """ Returns the Pure part of the Hybrid op. The Hybrid's effect is added to the ILOpholder.
        """
        hybrids = list()
        for h in operation.ops:
            if isinstance(h, Hybrid):
                hybrids.append(h)
        if len(hybrids) == 0:
            return operation

        tx_name = f't{self.hybrid_op_count}'
        tx = LocalVar(tx_name, operation.value_type)
        self.hybrid_op_count += 1

        # tx = <operation>
        name = f'op_{AssignmentType.ASSIGN.name}_{self.get_op_id()}'
        set_tx = Assignment(name, AssignmentType.ASSIGN, tx, operation)
        hybrids.insert(0, set_tx)

        # The Effect will be added to the ILOpHolder in the Effect constructor
        Sequence(f'seq_{self.get_op_id()}', hybrids)

        # Return local tX
        return tx
