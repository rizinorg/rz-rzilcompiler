# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.PluginInfo import (
    isa_to_reg_fnc,
    isa_to_reg_args,
    isa_explicit_to_op_args,
    isa_alias_to_op_args,
    isa_alias_to_op,
    isa_explicit_to_op,
)
from rzil_compiler.Transformer.Pures.GlobalVar import GlobalVar
from enum import StrEnum

from rzil_compiler.Transformer.Pures.Pure import ValueType


class RegisterAccessType(StrEnum):
    R = "SRC_REG"
    W = "DEST_REG"
    RW = "SRC_DEST_REG"
    PR = "SRC_REG_PAIR"
    PW = "DEST_REG_PAIR"
    PRW = "SRC_DEST_REG_PAIR"
    UNKNOWN = "UNKNOWN"


class Register(GlobalVar):
    def __init__(
        self,
        name: str,
        access: RegisterAccessType,
        v_type: ValueType,
        is_new: bool = False,
        is_explicit: bool = False,
        is_reg_alias: bool = False,
    ):
        self.access = access
        self.is_new = is_new
        self.is_reg_alias = is_reg_alias
        self.is_explicit = (
            is_explicit or is_reg_alias
        )  # Register number is predefined by instruction.

        if self.is_new:
            GlobalVar.__init__(self, name + "_new", v_type)
        else:
            GlobalVar.__init__(self, name, v_type)
        self.set_isa_name(name)

    def get_op_var(self):
        return self.name + "_op"

    def vm_id(self, write_usage: bool):
        if write_usage:
            return self.get_op_var()
        return self.get_op_var()

    def il_init_var(self):
        if self.get_name().lower() == "pc":
            # PC is never present as IL variable. Get it from the pkt.
            return "RzILOpPure *pc = U32(pkt->pkt_addr);"

        # Registers which are only written do not need their own RzILOpPure.
        if self.access == RegisterAccessType.W or self.access == RegisterAccessType.PW:
            return self.il_isa_to_assoc_name(True)
        elif (
            self.access == RegisterAccessType.RW
            or self.access == RegisterAccessType.PRW
        ):
            init = self.il_isa_to_assoc_name(True) + "\n"
        else:
            init = self.il_isa_to_assoc_name(False) + "\n"

        init += f"RzILOpPure *{self.pure_var()} = READ_REG({self.get_op_var()}, false);"
        return init

    def il_isa_to_assoc_name(self, write_usage: bool) -> str:
        """Returns code to: Translate a placeholder ISA name of an register (like Rs)
        to the real register name of the current instruction.
        E.g. Rs -> "R3"
        """
        if self.is_reg_alias:
            return self.il_reg_alias_to_op(write_usage)
        elif self.is_explicit:
            return self.il_explicit_reg_to_op(write_usage)
        return (
            f"const HexOp *{self.get_op_var()} = {isa_to_reg_fnc}("
            f'{", ".join(isa_to_reg_args)}'
            f", '{self.get_isa_name()[1]}'"
            f", {str(self.is_new or write_usage).lower()});"
        )

    def il_reg_alias_to_op(self, write_usage: bool) -> str:
        """Some registers are an alias for another register (PC = C9, GP = C11, SP = R29 etc.)
        Unfortunately those alias can change from ISA version to ISA version.
        So the plugin needs to translate these. Here we return the code for this translation.
        """
        return (
            f"const HexOp *{self.get_op_var()} = {isa_alias_to_op}("
            f'{", ".join(isa_alias_to_op_args)}'
            f'{", " if isa_alias_to_op_args else ""}{self.get_alias_enum(self.name)}'
            f", {str(self.is_new or write_usage).lower()});"
        )

    def il_explicit_reg_to_op(self, write_usage: bool) -> str:
        """Some registers are explicitly named (P0 etc.). Here we resolve them."""
        return (
            f"const HexOp *{self.get_op_var()} = {isa_explicit_to_op}("
            f'{", ".join(isa_explicit_to_op_args)}'
            f'{", " if isa_explicit_to_op_args else ""}{self.get_explicit_enum(self.name)}'
            f", {str(self.is_new or write_usage).lower()});"
        )

    def il_read(self) -> str:
        # There is a tricky case where write only register are read any ways in the semantic definitions.
        # We can detect those registers because Register.il_read() gets only called on readable registers.
        # So if this method is called on a write-only register we return the value of the .new register.
        # Examples: a2_svaddh, a4_vcmpbgt
        if self.access is RegisterAccessType.W or self.access is RegisterAccessType.PW:
            return f"READ_REG({self.vm_id(True)}, true)"
        if self.access == RegisterAccessType.UNKNOWN:
            self.access = RegisterAccessType.R
        return GlobalVar.il_read(self)

    def get_pred_num(self) -> int:
        num = self.get_name()[-1]
        if self.get_name()[0].upper() != "P" or num not in ["0", "1", "2", "3"]:
            raise NotImplementedError(
                f"This function should only called for explicit predicate register. This is {self.get_name()}"
            )
        return int(num)

    def add_write_property(self):
        """Adds the WRITE access property to the register.
        Useful if the register was only seen as read but gets a value assigned later.
        """
        if self.access == RegisterAccessType.R:
            self.access = RegisterAccessType.RW
        elif self.access == RegisterAccessType.PR:
            self.access = RegisterAccessType.PRW
        elif self.access == RegisterAccessType.UNKNOWN:
            if self.get_isa_name()[0] == "P":
                self.access = RegisterAccessType.PW
            else:
                self.access = RegisterAccessType.W

    @staticmethod
    def get_alias_enum(alias: str) -> str:
        return f"HEX_REG_ALIAS_{alias.upper()}"

    @staticmethod
    def get_explicit_enum(alias: str) -> str:
        return f"HEX_REG_EXPLICIT_{alias.upper()}"
