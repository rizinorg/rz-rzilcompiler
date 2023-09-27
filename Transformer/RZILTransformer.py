# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer, Token

from rzil_compiler.Transformer.Hybrids.SubRoutine import SubRoutine, SubRoutineCall
from rzil_compiler.Transformer.Pures.ReturnValue import ReturnValue
from rzil_compiler.Transformer.Pures.Parameter import Parameter
from rzil_compiler.ArchEnum import ArchEnum
from rzil_compiler.Transformer.Effects.Branch import Branch
from rzil_compiler.Transformer.Effects.Effect import Effect
from rzil_compiler.Transformer.Effects.Empty import Empty
from rzil_compiler.Transformer.Effects.ForLoop import ForLoop
from rzil_compiler.Transformer.Effects.Jump import Jump
from rzil_compiler.Transformer.Effects.MemStore import MemStore
from rzil_compiler.Transformer.Effects.NOP import NOP
from rzil_compiler.Transformer.Effects.Sequence import Sequence
from rzil_compiler.HexagonExtensions import (
    HexagonTransformerExtension,
    get_fcn_param_types,
)
from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid, HybridType, HybridSeqOrder
from rzil_compiler.Transformer.Hybrids.PostfixIncDec import PostfixIncDec
from rzil_compiler.Transformer.ILOpsHolder import ILOpsHolder
from rzil_compiler.Transformer.Pures.BitOp import BitOperationType, BitOp
from rzil_compiler.Transformer.Pures.BooleanOp import BooleanOpType, BooleanOp
from rzil_compiler.Transformer.Hybrids.Call import Call
from rzil_compiler.Transformer.Pures.Cast import Cast
from rzil_compiler.Transformer.Pures.CompareOp import CompareOp, CompareOpType
from rzil_compiler.Transformer.Pures.LetVar import LetVar
from rzil_compiler.Transformer.Pures.LocalVar import LocalVar
from rzil_compiler.Transformer.Pures.MemLoad import MemAccessType, MemLoad
from rzil_compiler.Transformer.Pures.Number import Number
from rzil_compiler.Transformer.Pures.Pure import Pure, PureType
from rzil_compiler.Transformer.ValueType import (
    ValueType,
    c11_cast,
    get_value_type_by_c_number,
)
from rzil_compiler.Transformer.Effects.Assignment import Assignment, AssignmentType
from rzil_compiler.Transformer.Pures.ArithmeticOp import ArithmeticOp, ArithmeticType
from rzil_compiler.Transformer.Pures.Register import Register
from rzil_compiler.Transformer.Pures.Sizeof import Sizeof
from rzil_compiler.Transformer.Pures.Ternary import Ternary
from rzil_compiler.Transformer.Pures.Variable import Variable
from rzil_compiler.Transformer.helper import flatten_list
from rzil_compiler.Transformer.helper_hexagon import (
    get_num_base_by_token,
)


class RZILTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """

    # Classes of Pures which should not be initialized in the C code.
    inlined_pure_classes = (Number, Sizeof, Cast)
    # Total count of hybrids seen during transformation
    hybrid_op_count = 0
    hybrid_effect_dict = dict()
    imm_set_effect_list = list()

    def __init__(
        self,
        arch: ArchEnum,
        sub_routines: dict[str:SubRoutine] = None,
        parameters: list[Parameter] = None,
        return_type: ValueType = None,
    ):
        self.arch = arch
        self.gcc_ext_effects = list()
        self.sub_routines: dict[str:SubRoutine] = (
            dict() if not sub_routines else sub_routines
        )
        self.return_type = return_type
        # List of parameters this transformer can take as given from outer scope.
        self.parameters: dict[str:Parameter] = (
            dict() if not parameters else {p.get_name(): p for p in parameters}
        )
        if (self.return_type and not self.parameters) or (
            not self.return_type and self.parameters
        ):
            raise ValueError(
                "If parameters and return type must be set or unset. But never just one of them."
            )

        self.il_ops_holder = ILOpsHolder()

        if self.arch == ArchEnum.HEXAGON:
            self.ext = HexagonTransformerExtension(self)
        else:
            raise NotImplementedError(
                f"Architecture {self.arch} has not Transformer extension."
            )
        super().__init__()

    def reset(self):
        self.ext.reset_flags()
        self.gcc_ext_effects.clear()
        self.hybrid_effect_dict.clear()
        self.imm_set_effect_list.clear()
        self.il_ops_holder.clear()
        self.return_type = None
        self.parameters.clear()
        self.sub_routines.clear()

    def update_sub_routines(self, new_routines: dict[str:SubRoutine]) -> None:
        self.sub_routines.update(new_routines)

    def get_op_id(self) -> int:
        return self.il_ops_holder.get_op_count()

    def add_op(self, op):
        if op.get_name() in self.parameters:
            raise ValueError(f"Operand {op.get_name()} already defined as parameter.")
        elif self.il_ops_holder.has_op(op.get_name()):
            return self.il_ops_holder.get_op_by_name(op.get_name())

        num_id = self.il_ops_holder.get_op_count()
        op.set_num_id(num_id)
        if isinstance(op, self.inlined_pure_classes):
            if not hasattr(op, "inlined"):
                NotImplementedError(f"{op} can not be inlined yet.")
            op.inlined = True

        if (
            not isinstance(op, Variable)
            and not isinstance(op, Register)
            and not isinstance(op, ReturnValue)
        ):
            # Those have already a unique name
            op.set_name(f"{op.get_name()}_{num_id}")
        self.il_ops_holder.add_op(op)
        return op

    def fbody(self, items):
        self.ext.set_token_meta_data("fbody")

        holder = self.il_ops_holder
        if holder.is_empty():
            return f"return NOP();"

        res = ""
        # We are at the top. Generate code.
        res += "\n// READ\n"
        for op in holder.read_ops.values():
            read_op = op.il_init_var()
            if not read_op:
                continue
            res += read_op + "\n"

        res += "\n// EXEC\n"
        for op in holder.exec_ops.values():
            if isinstance(op, Hybrid):
                continue
            exec_op = op.il_init_var()
            if not exec_op:
                continue
            res += exec_op + "\n"

        res += "\n// WRITE\n"
        for op in holder.write_ops.values():
            if isinstance(op, Hybrid):
                hybrid_init = op.il_init_var()
                if not hybrid_init:
                    continue
                res += hybrid_init + "\n"
                continue
            write_op = op.il_init_var()
            if not write_op:
                continue
            res += write_op + "\n"

        # Hybrids which have no parent in the AST
        left_hybrids = [
            self.hybrid_effect_dict.pop(hid)
            for hid in [k for k in self.hybrid_effect_dict.keys()]
        ]
        # Assign all effects without parent in the AST to the final instruction sequence.
        instruction_sequence = Sequence(
            f"instruction_sequence",
            [
                op
                for op in self.imm_set_effect_list
                + left_hybrids
                + flatten_list(items)
                + self.gcc_ext_effects
                if isinstance(op, Effect)
            ],
        )

        res += instruction_sequence.il_init_var() + "\n"
        res += f"\nreturn {instruction_sequence.effect_var()};"
        return res

    def jump_stmt(self, items):
        if items[0] == "return":
            # Set result of the expression.
            if self.il_ops_holder.has_op("ret_val"):
                ret_val = self.il_ops_holder.get_op_by_name("ret_val")
            else:
                ret_val = self.add_op(ReturnValue(self.return_type))
            return self.add_op(
                Assignment("set_return_val", AssignmentType.ASSIGN, ret_val, items[1])
            )
        return items  # Pass them upwards

    def relational_expr(self, items):
        self.ext.set_token_meta_data("relational_expr")
        return self.compare_op(items)

    def equality_expr(self, items):
        self.ext.set_token_meta_data("equality_expr")
        return self.compare_op(items)

    def reg_alias(self, items):
        self.ext.set_token_meta_data("reg")

        return self.add_op(self.ext.reg_alias(items))

    # SPECIFIC FOR: Hexagon
    def new_reg(self, items):
        self.ext.set_token_meta_data("new_reg")

        return self.add_op(self.ext.hex_reg(items, True))

    def explicit_reg(self, items):
        name = items[0]
        new = items[1] is not None
        self.ext.set_token_meta_data("explicit_reg", is_new=new)
        return self.add_op(
            self.ext.hex_reg(
                [
                    Token("REG_TYPE", name[0]),
                    Token("SRC_DEST_REG", str(name[1:])),
                    name,
                ],
                is_new=new,
                is_explicit=True,
            )
        )

    def reg(self, items):
        self.ext.set_token_meta_data("reg")

        return self.add_op(self.ext.reg(items))

    def imm(self, items):
        self.ext.set_token_meta_data("imm")
        name = items[0]
        if name in self.il_ops_holder.read_ops:
            return self.il_ops_holder.read_ops[name]

        imm = self.ext.imm(items)
        assignment = self.add_op(
            Assignment(
                f"imm_assign",
                AssignmentType.ASSIGN,
                imm,
                imm,
            )
        )
        self.imm_set_effect_list.append(assignment)
        return self.add_op(imm)

    def jump(self, items):
        self.ext.set_token_meta_data("jump")
        ta: Pure = items[1]
        return self.chk_hybrid_dep(self.add_op(Jump(f"jump_{ta.pure_var()}", ta)))

    def type_specifier(self, items):
        self.ext.set_token_meta_data("data_type")
        return self.ext.get_value_type_by_resource_type(items)

    def init_a_cast(self, val_type: ValueType, pure: Pure, cast_name: str = "") -> Pure:
        """
        Initializes and returns a Cast if the val_types and the pure.val_type
        mismatch. Otherwise, it simply returns the pure.
        """
        if val_type == pure.value_type:
            return pure
        if not cast_name:
            cast_name = f"cast_{val_type}"
        return self.add_op(Cast(cast_name, val_type, pure))

    def cast_expr(self, items):
        self.ext.set_token_meta_data("cast_expr")
        val_type = items[0]
        data = items[1]
        if data.value_type == val_type:
            return data

        if not isinstance(data, Cast):
            return self.init_a_cast(val_type, data)

        # Duplicate casts can be reduced to a single one.
        # We check this here
        if data.value_type.signed != val_type.signed:
            # Always cast if signs mismatch.
            return self.init_a_cast(val_type, data)

        cast_i = data
        # Skip consecutive casts of same type
        while (
            isinstance(cast_i, Cast)
            and val_type.signed == cast_i.value_type.signed
            and (
                (val_type >= cast_i.value_type >= cast_i.get_ops()[0].value_type)
                or (val_type <= cast_i.value_type <= cast_i.get_ops()[0].value_type)
            )
        ):
            # Drop cast
            self.il_ops_holder.rm_op_by_name(cast_i.get_name())
            cast_i = cast_i.get_ops()[0]

        return self.init_a_cast(val_type, cast_i)

    def number(self, items):
        # Numbers of the form -10ULL
        self.ext.set_token_meta_data("number")

        v_type = get_value_type_by_c_number(items)
        num_str = (str(items[0]) if items[0] else "") + str(items[1])
        name = f'const_{"neg" if items[0] == "-" else "pos"}{items[1]}{items[2] if items[2] else ""}'

        holder = self.il_ops_holder
        if name in holder.read_ops:
            return holder.read_ops[name]
        return self.add_op(
            Number(name, int(num_str, get_num_base_by_token(items[1])), v_type)
        )

    def declaration_specifiers(self, items):
        self.ext.set_token_meta_data("declaration_specifiers")
        specifier: str = items[0]
        t: ValueType = items[1]
        if specifier == "const":
            # Currently ignore that the variable should be constant.
            return t
        raise NotImplementedError(
            f"Type specifier {specifier} currently not supported."
        )

    def set_dest_type(self, assig: Assignment, t: ValueType) -> None:
        """For "<type> Assignment" declarations the Assignment gets parsed first.
        Afterwards the type. Here we update the type of the destination variable.
        """
        if assig.dest.type != PureType.LOCAL and assig.dest.type != PureType.LET:
            raise NotImplementedError(
                f"Updating the type of a {assig.dest.type} is not allowed."
            )
        assig.dest.set_value_type(t)
        assig.dest, assig.src = self.cast_operands(
            a=assig.dest, b=assig.src, immutable_a=True
        )

    def declaration(self, items):
        self.ext.set_token_meta_data("declaration")

        if len(items) != 2:
            raise NotImplementedError(
                f"Declarations without exactly two tokens are not supported."
            )
        if hasattr(items[0], "type") and items[0].type != "IDENTIFIER":
            # Declarations like: "TYPE <id>;" are only added to the ILOpholder list.
            # They get initialize when they first get set.
            self.add_op(Variable(items[1], items[0]))
            return self.chk_hybrid_dep(self.add_op(Empty(f"empty")))
        t: ValueType = items[0]
        if isinstance(items[1], Assignment):
            assg: Assignment = items[1]
            self.set_dest_type(assg, t)
            return assg
        elif isinstance(items[1], Sequence):
            # This is an assignment which has a hybrid dependency. Iterate over sequence ops and find Assignment.
            items[1]: Sequence
            for e in items[1].effects:
                if isinstance(e, Assignment):
                    self.set_dest_type(e, t)
                    return items[1]
            raise NotImplementedError(
                "declaration without Assignment are not implemented."
            )
        elif isinstance(items[1], str):
            if items[1] in self.il_ops_holder.read_ops:
                return self.il_ops_holder.read_ops[items[1]]
            return self.add_op(Variable(items[1], t))
        raise NotImplementedError(f"Declaration with items {items} not implemented.")

    def init_declarator(self, items):
        self.ext.set_token_meta_data("init_declarator")

        if len(items) != 2:
            raise NotImplementedError(
                f"Can not initialize an Init declarator with {len(items)} tokens."
            )
        if items[0] in self.il_ops_holder.read_ops:
            # variable was declared before.
            dest = self.il_ops_holder.read_ops[items[0]]
        else:
            # Variable was not declared before. The type is unknown.
            # Type is updated in declaration handler.
            dest = Variable(items[0], None)
            self.add_op(dest)
        op_type = AssignmentType.ASSIGN
        src: Pure = items[1]
        name = f"op_{op_type.name}"
        dest, src = self.cast_operands(a=dest, b=src, immutable_a=True)
        return self.chk_hybrid_dep(self.add_op(Assignment(name, op_type, dest, src)))

    def selection_stmt(self, items):
        self.ext.set_token_meta_data("selection_stmt")
        cond = items[1]
        then_seq = self.chk_hybrid_dep(
            self.add_op(Sequence(f"seq_then", flatten_list(items[2])))
        )
        name = f"branch"
        if items[0] == "if" and len(items) == 3:
            return self.chk_hybrid_dep(
                self.add_op(Branch(name, cond, then_seq, Empty(f"empty")))
            )
        elif items[0] == "if" and len(items) > 3 and items[3] == "else":
            else_seq = self.chk_hybrid_dep(
                self.add_op(Sequence(f"seq_else", flatten_list(items[4])))
            )
            return self.chk_hybrid_dep(
                self.add_op(Branch(name, cond, then_seq, else_seq))
            )
        else:
            raise NotImplementedError(f'"{items[0]}" branch not implemented.')

    def conditional_expr(self, items):
        self.ext.set_token_meta_data("conditional_expr")
        then_p, else_p = self.cast_operands(a=items[1], b=items[2], immutable_a=False)
        return self.add_op(Ternary(f"cond", items[0], then_p, else_p))

    def update_assign_src(self, assign: Assignment):
        """
        For Assignment expressions, we need to add a PureExec for the
        corresponding expressions. So Add for +=, SUB for -= etc.
        """
        if assign.assign_type == AssignmentType.ASSIGN:
            return
        elif assign.assign_type == AssignmentType.ASSIGN_ADD:
            assign.src = ArithmeticOp(
                f"op_ADD",
                assign.src,
                assign.dest,
                ArithmeticType.ADD,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_SUB:
            assign.src = ArithmeticOp(
                f"op_SUB",
                assign.src,
                assign.dest,
                ArithmeticType.SUB,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_MUL:
            assign.src = ArithmeticOp(
                f"op_MUL",
                assign.src,
                assign.dest,
                ArithmeticType.MUL,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_MOD:
            assign.src = ArithmeticOp(
                f"op_MOD",
                assign.src,
                assign.dest,
                ArithmeticType.MOD,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_DIV:
            assign.src = ArithmeticOp(
                f"op_DIV",
                assign.src,
                assign.dest,
                ArithmeticType.DIV,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_RIGHT:
            assign.src = BitOp(
                f"op_SHIFTR",
                assign.src,
                assign.dest,
                BitOperationType.RSHIFT,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_LEFT:
            assign.src = BitOp(
                f"op_SHIFTL",
                assign.src,
                assign.dest,
                BitOperationType.LSHIFT,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_AND:
            assign.src = BitOp(
                f"op_AND",
                assign.src,
                assign.dest,
                BitOperationType.AND,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_OR:
            assign.src = BitOp(
                f"op_OR",
                assign.src,
                assign.dest,
                BitOperationType.OR,
            )
        elif assign.assign_type == AssignmentType.ASSIGN_XOR:
            assign.src = BitOp(
                f"op_XOR",
                assign.src,
                assign.dest,
                BitOperationType.XOR,
            )
        else:
            raise NotImplementedError(f"Assign type {assign.assign_type} not handled.")
        self.add_op(assign.src)

    def assignment_expr(self, items):
        self.ext.set_token_meta_data("assignment_expr")

        dest: Pure = items[0]
        if isinstance(dest, Register) and dest.get_isa_name()[0] == "P":
            dname = dest.get_isa_name().upper()
            # Predicates need special handling.
            self.ext.set_token_meta_data(
                "pred_write",
                pred_num=dest.get_pred_num()
                if dname[1] in ["0", "1", "2", "3"]
                else -1,
            )
        op_type = AssignmentType(items[1])
        src: Pure = items[2]
        name = f"op_{op_type.name}"
        if op_type not in [
            AssignmentType.ASSIGN_MOD,
            AssignmentType.ASSIGN_RIGHT,
            AssignmentType.ASSIGN_LEFT,
        ]:
            dest, src = self.cast_operands(a=dest, b=src, immutable_a=True)
        assignment = Assignment(name, op_type, dest, src)
        self.update_assign_src(assignment)
        return self.chk_hybrid_dep(self.add_op(assignment))

    def additive_expr(self, items):
        result = self.simplify_arithmetic_expr(items)
        if result:
            return self.add_op(result)
        self.ext.set_token_meta_data("additive_expr")

        a = items[0]
        b = items[2]
        op_type = ArithmeticType(items[1])
        name = f"op_{op_type.name}"
        if op_type != ArithmeticType.MOD:
            # Modular operations don't need matching types.
            a, b = self.cast_operands(a=a, b=b, immutable_a=False)
        return self.add_op(ArithmeticOp(name, a, b, op_type))

    def multiplicative_expr(self, items):
        result = self.simplify_arithmetic_expr(items)
        if result:
            return self.add_op(result)
        self.ext.set_token_meta_data("multiplicative_expr")

        a = items[0]
        b = items[2]
        op_type = ArithmeticType(items[1])
        name = f"op_{op_type.name}"
        if op_type != ArithmeticType.MOD:
            # Modular operations don't need matching types.
            a, b = self.cast_operands(a=a, b=b, immutable_a=False)
        v = ArithmeticOp(name, a, b, op_type)
        return self.add_op(v)

    def and_expr(self, items):
        self.ext.set_token_meta_data("and_expr")

        return self.bit_operations(items, BitOperationType.AND)

    def inclusive_or_expr(self, items):
        self.ext.set_token_meta_data("inclusive_or_expr")

        return self.bit_operations(items, BitOperationType.OR)

    def exclusive_or_expr(self, items):
        self.ext.set_token_meta_data("exclusive_or_expr")

        return self.bit_operations(items, BitOperationType.XOR)

    def logical_and_expr(self, items):
        self.ext.set_token_meta_data("logical_and_expr")
        return self.boolean_expr(items)

    def logical_or_expr(self, items):
        self.ext.set_token_meta_data("logical_or_expr")
        return self.boolean_expr(items)

    def boolean_expr(self, items):
        if items[0] == "!":
            t = BooleanOpType(items[0])
            name = f"op_INV"
            v = BooleanOp(name, items[1], None, t)
        else:
            t = BooleanOpType(items[1])
            name = f"op_{t.name}"
            a = items[0]
            b = items[2] if len(items) == 3 else None
            if a and b:
                # No need to check for single operand operations.
                a, b = self.cast_operands(a=a, b=b, immutable_a=False)
            v = BooleanOp(name, a, b, t)
        return self.add_op(v)

    def shift_expr(self, items):
        self.ext.set_token_meta_data("shift_expr")
        return self.bit_operations(items, BitOperationType(items[1]))

    def unary_expr(self, items):
        self.ext.set_token_meta_data("unary_expr")

        if items[0] == "~":
            v = self.bit_operations(items, BitOperationType.NOT)
        elif items[0] == "-":
            v = self.bit_operations(items, BitOperationType.NEG)
        elif items[0] == "!":
            v = self.boolean_expr(items)
        else:
            raise NotImplementedError(f"Unary expression {items[0]} not handler.")
        return v

    def argument_expr_list(self, items):
        self.ext.set_token_meta_data("argument_expr_list")
        return flatten_list(items)

    def sub_routine(self, items):
        routine_name = items[0]
        if routine_name not in self.sub_routines:
            # Handle it in legacy c_call handler.
            return self.c_call(items)
        args = items[1:]
        sub_routine: SubRoutine = self.sub_routines[routine_name]
        casted_args = self.cast_sub_routine_args(
            sub_routine.get_name(), args, sub_routine.get_parameter_value_types()
        )

        return self.resolve_hybrid(
            self.add_op(SubRoutineCall(self.sub_routines[routine_name], casted_args))
        )

    def postfix_expr(self, items):
        self.ext.set_token_meta_data("postfix_expr")
        t = HybridType(items[1])
        name = f"op_{HybridType(items[1]).name}"
        if t == HybridType.INC or t == HybridType.DEC:
            op: LocalVar = items[0]
            return self.resolve_hybrid(
                self.add_op(PostfixIncDec(name, op, op.value_type, t))
            )
        else:
            raise NotImplementedError(f"Postfix expression {t} not handled.")

    def bit_operations(self, items: list, op_type: BitOperationType):
        self.ext.set_token_meta_data("bit_operations")

        if len(items) < 3:
            # Single operand bit operation e.g. ~
            a = items[1]
            name = f"op_{op_type.name}"
            v = BitOp(name, a, None, op_type)
            return self.add_op(v)
        a = items[0]
        b = items[2]
        name = f"op_{op_type.name}"
        if (a and b) and not (
            op_type == BitOperationType.RSHIFT or op_type == BitOperationType.LSHIFT
        ):
            a, b = self.cast_operands(a=a, b=b, immutable_a=False)
        v = BitOp(name, a, b, op_type)
        return self.add_op(v)

    def mem_store(self, items):
        self.ext.set_token_meta_data("mem_store")
        va = items[3]
        data: Pure = items[4]
        operation_value_type = ValueType(items[1] == "s", items[2])
        if operation_value_type != data.value_type:
            # STOREW determines from the data type how many bytes are written.
            # Cast the data type to the mem store type
            data = self.init_a_cast(operation_value_type, data)
        return self.chk_hybrid_dep(
            self.add_op(MemStore(f"ms_{data.get_name()}", va, data))
        )

    # SPECIFIC FOR: Hexagon
    def mem_load(self, items):
        self.ext.set_token_meta_data("mem_load")
        vt = ValueType(items[1] == "s", items[2])
        mem_acc_type = MemAccessType(vt, True)
        va = items[3]
        if not isinstance(va, Pure):
            va = self.il_ops_holder.get_op_by_name(va.value)

        return self.add_op(MemLoad(f"ml_{va.get_name()}", va, mem_acc_type))

    def cast_sub_routine_args(
        self, fcn_name: str, args: list[Pure], predefined_types: list[ValueType] = None
    ) -> list[Pure]:
        if predefined_types:
            param_types = predefined_types
        else:
            param_types = get_fcn_param_types(fcn_name)
        if len(args) != len(param_types):
            raise NotImplementedError("Not all ops have a type assigned.")
        for i, (param, a_type) in enumerate(zip(args, param_types)):
            if isinstance(param, str):
                continue
            if not a_type or param.value_type == a_type:
                continue

            args[i] = self.init_a_cast(a_type, param, "param_cast")
        return args

    def c_call(self, items):
        self.ext.set_token_meta_data("c_call")
        prefix = items[0]
        if prefix == "sizeof":
            op = items[1]
            return self.add_op(Sizeof(f"op_sizeof_{op.get_name()}", op))
        val_type = self.ext.get_val_type_by_fcn(prefix)
        param = self.cast_sub_routine_args(prefix, items[1:])

        return self.resolve_hybrid(
            self.add_op(Call(f"c_call", val_type, [prefix] + param))
        )

    def identifier(self, items):
        self.ext.set_token_meta_data("identifier")
        # Hexagon shortcode can initialize certain variables without type.
        # Those are converted to a local var here.
        identifier = items[0].value
        if identifier in self.parameters:
            return self.parameters[identifier]

        holder = self.il_ops_holder
        if identifier in holder.read_ops:
            return holder.read_ops[identifier]
        if self.ext.is_special_id(identifier):
            return self.add_op(self.ext.special_identifier_to_local_var(identifier))
        # Return string. It could be a variable or a function call.
        return identifier

    def compare_op(self, items):
        self.ext.set_token_meta_data("compare_op")
        op_type = CompareOpType(items[1])
        a, b = self.cast_operands(a=items[0], b=items[2], immutable_a=False)
        return self.add_op(CompareOp(f"op_{op_type.name}", a, b, op_type))

    def for_loop(self, items):
        self.ext.set_token_meta_data("for_loop")
        if len(items) != 5:
            raise NotImplementedError(
                f"For loops with {len(items)} elements is not supported yet."
            )
        compound = self.chk_hybrid_dep(
            self.add_op(Sequence(f"seq", flatten_list(items[4]) + [items[3]]))
        )
        return self.chk_hybrid_dep(
            self.add_op(
                Sequence(
                    f"seq",
                    [items[1], self.add_op(ForLoop(f"for", items[2], compound))],
                )
            )
        )

    def iteration_stmt(self, items):
        self.ext.set_token_meta_data("iteration_stmt")
        if items[0] == "for":
            return self.for_loop(items)
        else:
            raise NotImplementedError(f"{items[0]} loop not supported.")

    def compound_stmt(self, items):
        self.ext.set_token_meta_data("compound_stmt")
        # These are empty compound statements.
        return self.chk_hybrid_dep(self.add_op(Empty(f"empty")))

    def gcc_extended_expr(self, items):
        self.ext.set_token_meta_data("gcc_extended_expr")
        if isinstance(items[0], list) and isinstance(items[-1], Pure):
            raise NotImplementedError(
                "List of statements in gcc extended expressions not implemented."
            )
        elif isinstance(items[0], list) or not items[1]:
            # This is a compound statement.
            return items[0]

        self.gcc_ext_effects.append(self.chk_hybrid_dep(items[0]))
        return items[1]  # expression

    def expr_stmt(self, items):
        self.ext.set_token_meta_data("expr_stmt")
        # These are empty expression statements.
        return self.add_op(self.chk_hybrid_dep(self.add_op(Empty(f"empty"))))

    def cancel_slot_stmt(self, items):
        self.ext.set_token_meta_data("cancel_slot_stmt")
        return self.add_op(self.chk_hybrid_dep(self.add_op(NOP(f"nop"))))

    def block_item_list(self, items):
        self.ext.set_token_meta_data("block_item_list")
        return items

    def block_item(self, items):
        self.ext.set_token_meta_data("block_item")
        return items[0]

    def chk_hybrid_dep(self, effect: Effect) -> Effect:
        """Check hybrid dependency. Checks if a hybrid effect must be executed before the given effect and returns
        a sequence of Sequence(hybrid, given effect) if so. Otherwise, the original effect.
        """
        if len(self.hybrid_effect_dict) == 0:
            return effect
        hybrid_deps = list()
        for o in effect.get_op_list():
            if not isinstance(o, str) and o.get_name() in self.hybrid_effect_dict:
                hybrid_deps.append(self.hybrid_effect_dict.pop(o.get_name()))

        if len(hybrid_deps) == 0:
            return effect
        return self.add_op(Sequence(f"seq", hybrid_deps + [effect]))

    def resolve_hybrid(self, hybrid: Hybrid) -> Pure:
        """Splits a hybrid in a Pure and Effect part.
        The Pure is assigned to a LocalVar. The LocalVar gets returned.
        The hybrids effect and the assignment of the LocalVar are saved to a list and used later when
        the dependent effect is created.
        """
        tmp_x_name = f"h_tmp{self.hybrid_op_count}"
        tmp_x = LocalVar(tmp_x_name, hybrid.value_type)
        self.hybrid_op_count += 1

        # Assign the hybrid pure part to tmp_x.
        name = f"op_{AssignmentType.ASSIGN.name}_hybrid_tmp"
        tmp_x, hybrid = self.cast_operands(a=tmp_x, b=hybrid, immutable_a=True)
        set_tmp = self.add_op(Assignment(name, AssignmentType.ASSIGN, tmp_x, hybrid))

        # Add hybrid effect to the ILOpHolder in the Effect constructor.
        if hybrid.seq_order == HybridSeqOrder.SET_VAL_THEN_EXEC:
            h_seq = [set_tmp, hybrid]
        elif hybrid.seq_order == HybridSeqOrder.EXEC_THEN_SET_VAL:
            h_seq = [hybrid, set_tmp]
        else:
            raise NotImplementedError(
                f"Hybrid {hybrid} has no valid sequence order set."
            )

        seq = self.add_op(Sequence(f"seq", h_seq))
        seq = self.chk_hybrid_dep(seq)

        self.hybrid_effect_dict[tmp_x_name] = seq
        # Return local tX
        return tmp_x

    def simplify_arithmetic_expr(self, items) -> Pure:
        """
        Checks if the given arithmetic expression can be simplified.
        Simple arithmetic expressions can be resolved to a single number,
        so we do not have to do it during runtime.
        """
        a = items[0]
        operation: str = items[1]
        b = items[2]
        if not isinstance(a, LetVar) or not isinstance(b, LetVar):
            return None

        if not isinstance(a.get_val(), int) or not isinstance(b.get_val(), int):
            return None

        val_a = a.get_val()
        val_b = b.get_val()
        self.il_ops_holder.rm_op_by_name(a.get_name())
        self.il_ops_holder.rm_op_by_name(b.get_name())
        match operation:
            case "+":
                result = val_a + val_b
            case "-":
                result = val_a - val_b
            case "*":
                result = val_a * val_b
            case "/":
                result = val_a / val_b
            case _:
                raise NotImplementedError(f"Can not simplify '{operation}' expression.")
        a_type, b_type = c11_cast(a.value_type, b.value_type)

        name = f'const_{"neg" if items[0] == "-" else "pos"}{items[1]}{items[2] if items[2] else ""}'
        return Number(name, result, a_type)

    def cast_operands(self, immutable_a: bool, **ops) -> tuple[Pure, Pure]:
        """Casts two operands to a common type according to C11 standard.
        If immutable_op_a = True operand b is cast to the operand a type
        (Useful for assignments to global vars like registers).
        Operand are names in the order: a, b, c, ...
        """
        if "a" not in ops and "b" not in ops:
            raise NotImplementedError('At least operand "a" and "b" must e given.')
        a = ops["a"]
        b = ops["b"]
        if not a.value_type and not b.value_type:
            raise NotImplementedError("Cannot cast ops without value types.")
        if not a.value_type:
            a.value_type = b.value_type
            return a, b
        if not b.value_type:
            b.value_type = a.value_type
            return a, b

        if a.value_type == b.value_type:
            return a, b

        if immutable_a:
            return a, self.init_a_cast(a.value_type, b)

        casted_a, casted_b = c11_cast(a.value_type, b.value_type)

        if (
            casted_a.bit_width != a.value_type.bit_width
            or casted_a.signed != a.value_type.signed
        ):
            a = self.init_a_cast(casted_a, a)
        if (
            casted_b.bit_width != b.value_type.bit_width
            or casted_b.signed != b.value_type.signed
        ):
            b = self.init_a_cast(casted_b, b)

        return a, b
