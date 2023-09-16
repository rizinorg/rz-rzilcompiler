# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Transformer, Token

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
    get_fcn_arg_types,
)
from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid, HybridType, HybridSeqOrder
from rzil_compiler.Transformer.Hybrids.PostfixIncDec import PostfixIncDec
from rzil_compiler.Transformer.ILOpsHolder import ILOpsHolder
from rzil_compiler.Transformer.Pures.BitOp import BitOperationType, BitOp
from rzil_compiler.Transformer.Pures.BooleanOp import BooleanOpType, BooleanOp
from rzil_compiler.Transformer.Hybrids.Call import Call
from rzil_compiler.Transformer.Pures.Cast import Cast
from rzil_compiler.Transformer.Pures.CompareOp import CompareOp, CompareOpType
from rzil_compiler.Transformer.Pures.LocalVar import LocalVar
from rzil_compiler.Transformer.Pures.MemLoad import MemAccessType, MemLoad
from rzil_compiler.Transformer.Pures.Number import Number
from rzil_compiler.Transformer.Pures.Pure import Pure, ValueType, PureType
from rzil_compiler.Transformer.Effects.Assignment import Assignment, AssignmentType
from rzil_compiler.Transformer.Pures.ArithmeticOp import ArithmeticOp, ArithmeticType
from rzil_compiler.Transformer.Pures.Register import Register
from rzil_compiler.Transformer.Pures.Sizeof import Sizeof
from rzil_compiler.Transformer.Pures.Ternary import Ternary
from rzil_compiler.Transformer.Pures.Variable import Variable
from rzil_compiler.Transformer.helper import flatten_list, c11_cast
from rzil_compiler.Transformer.helper_hexagon import (
    get_value_type_by_c_number,
    get_num_base_by_token,
)


class RZILTransformer(Transformer):
    """
    Transforms the tree into Pures and Effects.
    The classes do the actual code generation.
    """

    # Total count of hybrids seen during transformation
    hybrid_op_count = 0
    hybrid_effect_dict = dict()
    imm_set_effect_list = list()

    def __init__(self, arch: ArchEnum):
        self.arch = arch
        self.gcc_ext_effects = list()
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

    def get_op_id(self) -> int:
        return self.il_ops_holder.get_op_count()

    def add_op(self, op):
        if not self.il_ops_holder.has_op(op.get_name()):
            if not isinstance(op, Variable) and not isinstance(op, Register):
                # Those have already a unique name
                op.set_name(f"{op.get_name()}_{self.il_ops_holder.get_op_count()}")
            self.il_ops_holder.add_op(op)
            return op
        return self.il_ops_holder.get_op_by_name(op.get_name())

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
        if name == "R31":
            # We don't know whether R31 is used as dest or src. Hence: SRC_DEST_REG.
            return self.add_op(
                self.ext.hex_reg(
                    [Token("REG_TYPE", "R"), Token("SRC_DEST_REG", "31"), name],
                    is_new=new,
                    is_explicit=True,
                )
            )
        elif name[0] == "P":
            return self.add_op(
                self.ext.hex_reg(
                    [Token("REG_TYPE", "P"), Token("SRC_DEST_REG", str(name[1])), name],
                    is_new=new,
                    is_explicit=True,
                )
            )
        else:
            raise NotImplementedError(f"Explicit register {items} not handled.")

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

    def cast_expr(self, items):
        self.ext.set_token_meta_data("cast_expr")
        val_type = items[0]
        data = items[1]
        if not isinstance(data, Cast):
            return self.add_op(Cast(f"cast_{val_type}", val_type, data))

        # Duplicate casts can be reduced to a single one.
        # We check this here
        if data.value_type.signed != val_type.signed:
            return self.add_op(Cast(f"cast_{val_type}", val_type, data))

        prev_cast_ops = data.get_ops()
        assert len(prev_cast_ops) == 1
        self.il_ops_holder.rm_op_by_name(data.get_name())
        return self.add_op(Cast(f"cast_{val_type}", val_type, prev_cast_ops[0]))

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
        return self.chk_hybrid_dep(self.add_op(Assignment(name, op_type, dest, src)))

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
            name = f"op_{t}"
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
            data = Cast(f"op", operation_value_type, data)
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

    def cast_call_params(self, fcn_name: str, args: list[Pure]) -> list[Pure]:
        arg_types = get_fcn_arg_types(fcn_name)
        if len(args) != len(arg_types):
            raise NotImplementedError("Not all ops have a type assigned.")
        for i, (arg, a_type) in enumerate(zip(args, arg_types)):
            if isinstance(arg, str):
                continue
            if not a_type or arg.value_type == a_type:
                continue

            args[i] = self.add_op(Cast(f"arg_cast", a_type, arg))
        return args

    def c_call(self, items):
        self.ext.set_token_meta_data("c_call")
        prefix = items[0]
        if prefix == "sizeof":
            op = items[1]
            return self.add_op(Sizeof(f"op_sizeof_{op.get_name()}", op))
        val_type = self.ext.get_val_type_by_fcn(prefix)

        fcn_name = items[0]
        param = self.cast_call_params(fcn_name, items[1:])
        return self.resolve_hybrid(
            self.add_op(Call(f"c_call", val_type, [fcn_name] + param))
        )

    def identifier(self, items):
        self.ext.set_token_meta_data("identifier")
        # Hexagon shortcode can initialize certain variables without type.
        # Those are converted to a local var here.
        identifier = items[0].value
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
        if not isinstance(a, Number) or not isinstance(b, Number):
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

        cname = f"cast"
        if immutable_a:
            return a, self.add_op(Cast(cname, a.value_type, b))

        casted_a, casted_b = c11_cast(a.value_type, b.value_type)

        if (
            casted_a.bit_width != a.value_type.bit_width
            or casted_a.signed != a.value_type.signed
        ):
            a = self.add_op(Cast(cname, casted_a, a))
        if (
            casted_b.bit_width != b.value_type.bit_width
            or casted_b.signed != b.value_type.signed
        ):
            b = self.add_op(Cast(cname, casted_b, b))

        return a, b
