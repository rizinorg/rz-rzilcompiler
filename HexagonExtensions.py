# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import re

from Helper import log
from rzil_compiler.CompilerExtension import CompilerExtension
from rzil_compiler.Transformer.Pures.Immediate import Immediate
from rzil_compiler.Transformer.ValueType import (
    ValueType,
    get_value_type_from_reg_type,
    get_value_type_by_isa_imm,
    VTGroup,
    get_value_type_by_c_type,
)
from rzil_compiler.Transformer.Pures.Register import RegisterAccessType, Register
from rzil_compiler.Transformer.Pures.Variable import Variable
from rzil_compiler.Transformer.TransformerExtension import TransformerExtension
from lark import Token, Tree


class HexagonTransformerExtension(TransformerExtension):
    uses_new = False
    writes_mem = False
    reads_mem = False
    is_conditional = False
    branches = False
    writes_predicate = False
    preds_written = list()  # The numbers of the predicate registers written.

    def __init__(self, transformer):
        # Variables names used in the shortcode with special meaning.
        self.spec_ids = {"EffectiveAddress": "EA", "iterator_vars": ["i", "k", "j"]}
        self.transformer = transformer
        self.missing_fcns = dict()

    def report_missing_fcns(self):
        log("Missing functions:")
        for k, v in self.missing_fcns.items():
            print(f"\t{k} = {v}")
        print(f"\tsum = {sum(self.missing_fcns.values())}")

    def set_uses_new(self):
        if not self.uses_new:
            self.uses_new = True

    def set_writes_pred(self, num: int):
        if not self.writes_predicate:
            self.writes_predicate = True
        if num in range(4) and num not in self.preds_written:
            self.preds_written.append(num)

    def set_writes_mem(self):
        if not self.writes_mem:
            self.writes_mem = True

    def set_reads_mem(self):
        if not self.reads_mem:
            self.reads_mem = True

    def set_is_conditional(self):
        if not self.is_conditional:
            self.is_conditional = True

    def set_branches(self):
        if not self.branches:
            self.branches = True

    def reset_flags(self):
        self.is_conditional = False
        self.reads_mem = False
        self.writes_mem = False
        self.writes_predicate = False
        self.uses_new = False
        self.branches = False

    def set_token_meta_data(self, token: str, **kwargs):
        if token == "mem_store":
            self.set_writes_mem()
        elif token == "mem_load":
            self.set_reads_mem()
        elif token == "new_reg":
            self.set_uses_new()
        elif token == "jump":
            self.set_branches()
        elif token == "selection_stmt":
            self.set_is_conditional()
        elif token == "explicit_reg":
            if kwargs["is_new"]:
                self.set_uses_new()
        elif token == "pred_write":
            if len(kwargs) != 1:
                raise NotImplementedError(
                    "If a predicate is written it always needs to give its number."
                )
            num = kwargs["pred_num"]
            self.set_writes_pred(num)

    def reg_alias(self, items):
        alias = items[0].lower()
        is_new = False

        if items[1]:
            is_new = True
            self.set_token_meta_data("new_reg")
        holder = self.transformer.il_ops_holder
        given_name = f"{alias}{'_new' if is_new else ''}"
        if given_name in holder.read_ops:
            return holder.read_ops[given_name]

        if alias == "upcycle" or alias == "pktcount" or alias == "utimer":
            size = 64
        else:
            size = 32
        v_type = ValueType(False, size)
        # Access type is unknown. For Alias the access type is set when it is part
        # of another pure or an effect.
        return Register(
            alias, RegisterAccessType.UNKNOWN, v_type, is_new=is_new, is_reg_alias=True
        )

    def reg(self, items):
        return self.hex_reg(items, False)

    def hex_reg(self, items, is_new: bool, is_explicit: bool = False):
        holder = self.transformer.il_ops_holder
        items: [Token]
        if is_explicit:
            # If the register is explicitly given (R31, P1, P2 etc.)
            # The name is always the last in the list.
            name = items[-1]
        else:
            name = "".join(items)

        if is_explicit:
            access_t = RegisterAccessType.UNKNOWN
        else:
            access_t = RegisterAccessType(items[1].type)  # src, dest, both
        v_type = get_value_type_from_reg_type(items)

        v = Register(
            name, access=access_t, v_type=v_type, is_new=is_new, is_explicit=is_explicit
        )
        return v

    def imm(self, items):
        v_type = get_value_type_by_isa_imm(items)
        name = items[0]
        imm = Immediate(name, v_type)
        return imm

    def get_value_type_by_resource_type(self, items):
        if items[0] == "int":
            return ValueType(True, 32)
        elif items[0] == "unsigned" or (
            len(items) == 2 and items[0] == "unsigned" and items[1] == "int"
        ):
            return ValueType(False, 32)
        items: Tree = items[0]
        if not hasattr(items, "data"):
            raise NotImplementedError(f"Data type {items} is not handled.")
        rule = items.data
        tokens = items.children
        if rule == "c_size_type":
            return ValueType(tokens[1] == "s", int(tokens[0]) * 8)
        elif rule == "c_int_type":
            return ValueType(tokens[0] == "int", int(tokens[1]))
        else:
            raise NotImplementedError(f"Data type {rule} is not handled.")

    def get_meta(self) -> list[str]:
        flags = []
        if self.is_conditional:
            flags.append("HEX_IL_INSN_ATTR_COND")
        if self.uses_new:
            flags.append("HEX_IL_INSN_ATTR_NEW")
        if self.writes_mem:
            flags.append("HEX_IL_INSN_ATTR_MEM_WRITE")
        if self.reads_mem:
            flags.append("HEX_IL_INSN_ATTR_MEM_READ")
        if self.branches:
            flags.append("HEX_IL_INSN_ATTR_BRANCH")
        if self.writes_predicate:
            flags.append("HEX_IL_INSN_ATTR_WPRED")
            for p in self.preds_written:
                flags.append(f"HEX_IL_INSN_ATTR_WRITE_P{p}")
        if len(flags) == 0:
            flags.append("HEX_IL_INSN_ATTR_NONE")

        return flags

    def get_noped_meta(self):
        """ Returns the meta information about a noped instruction."""
        return ["HEX_IL_INSN_ATTR_NONE"]

    def get_val_type_by_fcn(self, fcn_name: str):
        if fcn_name == "get_npc":
            return ValueType(False, 32)
        elif fcn_name == "STORE_SLOT_CANCELLED":
            # Marks the slot i as cancelled in a global variable for this case.
            # returns void.
            return ValueType(False, 32, group=VTGroup.VOID)
        elif fcn_name == "WRITE_REG":
            return ValueType(False, 32, VTGroup.VOID)
        else:
            if fcn_name not in self.missing_fcns:
                self.missing_fcns[fcn_name] = 1
            else:
                self.missing_fcns[fcn_name] += 1
            raise NotImplementedError(f"No value type for function {fcn_name} defined.")

    def is_special_id(self, ident: str) -> bool:
        if ident == self.spec_ids["EffectiveAddress"]:
            return True
        elif ident in self.spec_ids["iterator_vars"]:
            return True
        else:
            return False

    def special_identifier_to_local_var(self, identifier):
        if identifier == self.spec_ids["EffectiveAddress"]:
            return Variable("EA", ValueType(False, 32))
        elif identifier in self.spec_ids["iterator_vars"]:
            return Variable(identifier, ValueType(False, 32))
        raise NotImplementedError(f"Special identifier {identifier} not handled.")


class HexagonCompilerExtension(CompilerExtension):
    def transform_insn_name(self, insn_name) -> str:
        if "sa2_tfrsi" in insn_name.lower():
            # SA2_tfrsi is the sub-instruction equivalent to A2_tfrsi.
            # But it is not documented and not in the shortcode.
            return "A2_tfrsi"
        if insn_name[:2] == "X2":
            raise NotImplementedError(
                "Can not compiler duplex instructions because they are not given in the shortcode."
            )
        if re.match(r"^.+_undocumented$", insn_name):
            return insn_name[:-13]
        elif re.match(r"^undocumented_.+$", insn_name):
            return insn_name[13:]
        elif re.match(f"^IMPORTED_", insn_name):
            return insn_name[9:]
        elif re.match(r"^dep_", insn_name):
            return insn_name[4:]
        else:
            return insn_name


def get_fcn_param_types(fcn_name: str) -> [ValueType]:
    """Returns a list of ValueTypes for each function argument (from left to right).
    If an argument has no IL type (strings for example) the type is None.
    """
    if fcn_name == "get_npc":
        return [None]
    elif fcn_name == "WRITE_PRED":
        return [ValueType(False, 8), ValueType(False, 8)]
    elif fcn_name == "STORE_SLOT_CANCELLED":
        # Marks the slot i as cancelled in a global variable for this case.
        return [ValueType(False, 32, VTGroup.EXTERNAL, "HexPkt *"), ValueType(False, 8)]
    elif fcn_name == "WRITE_REG":
        return [
            get_value_type_by_c_type("HexPktInsnBundle"),
            get_value_type_by_c_type("HexOp"),
            get_value_type_by_c_type("uint32_t"),
        ]
    else:
        raise NotImplementedError(
            f"No value type for the function parameter of {fcn_name} defined."
        )
