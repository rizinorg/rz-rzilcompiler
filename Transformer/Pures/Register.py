# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import re

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

from rzil_compiler.Transformer.ValueType import ValueType


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
        self.set_isa_name(self.name)
        self.reg_number = self.get_reg_num_from_name(self.get_isa_name())
        self.reg_class = self.get_reg_class()

    def get_op_var(self, deref=True):
        var = self.name + "_op"
        var = var.replace(":", "_")
        if deref and (self.is_explicit or self.is_reg_alias):
            # Operand variables of alias and explicit regs should be passed as pointer.
            return f"&{var}"
        return var

    def vm_id(self):
        return self.get_op_var()

    def pure_var(self):
        var = GlobalVar.pure_var(self)
        return var.replace(":", "_")

    def il_init_var(self):
        if self.get_name() == "pc":
            return "RzILOpPure *pc = U32(pkt->pkt_addr);"
        # Registers which are only written do not need their own RzILOpPure.
        if self.access == RegisterAccessType.W or self.access == RegisterAccessType.PW:
            return self.il_isa_to_assoc_name()
        else:
            init = self.il_isa_to_assoc_name() + "\n"

        init += f"RzILOpPure *{self.pure_var()} = READ_REG(pkt, {self.get_op_var()}, {str(self.is_new).lower()});"
        return init

    def il_isa_to_assoc_name(self) -> str:
        if self.is_reg_alias:
            return self.il_reg_alias_to_op()
        elif self.is_explicit:
            return self.il_explicit_reg_to_op()
        return (
            f"const HexOp *{self.get_op_var()} = {isa_to_reg_fnc}("
            f'{", ".join(isa_to_reg_args)}'
            f", '{self.get_isa_name()[1]}'"
            f", {str(self.is_new).lower()});"
        )

    def il_reg_alias_to_op(self) -> str:
        """Some registers are an alias for another register (PC = C9, GP = C11, SP = R29 etc.)
        Unfortunately those alias can change from ISA version to ISA version.
        So the plugin needs to translate these. Here we return the code for this translation.
        """
        return (
            f"const HexOp {self.get_op_var(deref=False)} = {isa_alias_to_op}("
            f'{", ".join(isa_alias_to_op_args)}'
            f'{", " if isa_alias_to_op_args else ""}{self.get_alias_enum()}'
            f", {str(self.is_new).lower()});"
        )

    def il_explicit_reg_to_op(self) -> str:
        """Some registers are explicitly named (P0 etc.). Here we resolve them."""
        assert self.reg_number is not None
        return (
            f"const HexOp {self.get_op_var(deref=False)} = {isa_explicit_to_op}("
            f'{", ".join(isa_explicit_to_op_args)}'
            f'{", " if isa_explicit_to_op_args else ""}'
            f"{self.reg_number}, {self.reg_class}"
            f", {str(self.is_new).lower()});"
        )

    def il_read(self) -> str:
        # There is a tricky case where write only register are read any ways in the semantic definitions.
        # We can detect those registers because Register.il_read() gets only called on readable registers.
        # So if this method is called on a write-only register we return the value of the .new register.
        # Examples: a2_svaddh, a4_vcmpbgt
        if self.access is RegisterAccessType.W or self.access is RegisterAccessType.PW:
            return f"READ_REG(pkt, {self.get_op_var()}, false)"
        if self.access == RegisterAccessType.UNKNOWN:
            self.access = RegisterAccessType.R
        return GlobalVar.il_read(self).replace(":", "_")

    def get_pred_num(self) -> int:
        num = re.findall(r"\d", self.get_name())[0]
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

    def get_alias_enum(self) -> str:
        name = self.get_name().upper()
        if self.is_new:
            name = name.replace("_NEW", "")
        return f"HEX_REG_ALIAS_{name}"

    def get_reg_class(self) -> str | None:
        """
        Returns the name of the LLVM register class this register belongs to.

        :return: The register class name or None if not handled (e.g. for alias)
        """
        if self.is_reg_alias:
            return None

        reg_name = self.get_isa_name()
        reg_class = "HEX_REG_CLASS_"
        match reg_name[0].upper():
            case "R" | "N":
                reg_class += "INT_REGS"
            case "P":
                reg_class += "PRED_REGS"
            case "V":
                reg_class += "HVX_VR"
            case "Q":
                reg_class += "HVX_QR"
            case "G":
                reg_class += "GUEST_REGS"
            case "S":
                reg_class += "SYS_REGS"
            case "M":
                reg_class += "MOD_REGS"
            case "C":
                reg_class += "CTR_REGS"
            case _:
                raise ValueError(f"Register {reg_name} has no class assigned.")

        is_double = ":" in reg_name or (
            len(reg_name) > 2 and reg_name[1] == reg_name[2]
        )
        if is_double:
            if reg_name[0] == "R":
                return "HEX_REG_CLASS_DOUBLE_REGS"
            elif reg_name[0] == "V":
                return "HEX_REG_CLASS_HVX_WR"
            elif reg_name[0] == "Q":
                raise ValueError(f"Doble vector predicates not yet handled: {reg_name}")
            return reg_class + "64"
        return reg_class

    @staticmethod
    def get_reg_num_from_name(reg_name: str) -> int | None:
        """
        Determines the register number from the name.
        :param reg_name: The name of the register 'Rd', 'P0', 'V31:30' etc.
        :return: The number of the register as in Rizins enums or None if no number can be retrieved (e.g. for 'Rd').
        """
        num = None
        for n in re.findall(r"\d+", reg_name):
            # For double registers, the smaller number is the number in the enums.
            num = min(num, int(n)) if num else int(n)
        return num
