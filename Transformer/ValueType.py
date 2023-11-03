import re
from copy import deepcopy
from enum import Flag, auto, StrEnum

from lark import Token

from rzil_compiler.Transformer.helper_hexagon import get_num_base_by_token


class VTGroup(Flag):
    PURE = auto()  # Normal Pure value
    BOOL = auto()  # PureBool type: bitWidth = 1; 1 == true 0 == false
    HYBRID_LVAR = (
        auto()
    )  # A hybrid LocalVar consumed by operands which use the return value of a hybrid
    EXTERNAL = auto()  # ValueType not known and used by the VM.
    ARCH_LONG = (
        auto()
    )  # ValueType has the same bit-width as a long on the current architecture (used for varying bit
    # supporting architectures).
    VOID = auto()  # A void type.
    CONST = auto()  # A constant type
    FLOAT = auto()  # A float number
    DOUBLE = auto()  # A float number
    IEEE = auto()  # A number following the IEEE standard (relevant for float).

    @staticmethod
    def get_external_types() -> list[str]:
        return [
            "HexOp",
            "HexInsnPktBundle",
            "HexInsn",
            "HexPkt",
            "RzILOpEffect",
            "RzFloatFormat",
            "HexRegFieldProperty",
            "HexRegField"
        ]


class FloatFormat(StrEnum):
    IEEE754_BIN_16 = "IEEE754_BIN_16"
    IEEE754_BIN_32 = "IEEE754_BIN_32"
    IEEE754_BIN_64 = "IEEE754_BIN_64"
    IEEE754_BIN_80 = "IEEE754_BIN_80"
    IEEE754_BIN_128 = "IEEE754_BIN_128"
    IEEE754_DEC_64 = "IEEE754_DEC_64"
    IEEE754_DEC_128 = "IEEE754_DEC_128"

    @staticmethod
    def rzil_repr(float_form: str) -> str:
        return f"RZ_FLOAT_{float_form}"


class ValueType:
    """Is used to match value against their UN() and SN() equivalence."""

    def __init__(
        self,
        signed: bool,
        bit_width: int,
        group: VTGroup = VTGroup.PURE,
        external_type: str = None,
        format: FloatFormat | None = None,
    ):
        self._signed = signed
        self._bit_width = bit_width
        self.group: VTGroup = group
        self.format = format
        self.external_type: str = external_type
        if self.group & VTGroup.EXTERNAL and not self.external_type:
            raise ValueError(
                "If the ValueTypeGroup is EXTERNAL a type name must be given as well."
            )
        if (
            self.group & (VTGroup.FLOAT | VTGroup.DOUBLE)
            and not self.group & VTGroup.IEEE
        ):
            raise ValueError(
                "Double and floats need a standard assigned as well (like VTGroup.IEEE)."
            )
        if (self.group & VTGroup.IEEE) and not self.format:
            raise ValueError(
                f"If this ValueType follows an IEEE standard, the format must be given as well."
            )

    @property
    def signed(self) -> bool:
        if self.group & VTGroup.EXTERNAL or self.group & VTGroup.VOID:
            raise ValueError(
                f"ValueType {self} is of type {self.group}. "
                f"The signed flag should not be used on those groups."
            )
        return self._signed

    @signed.setter
    def signed(self, val):
        if self.group & VTGroup.EXTERNAL or self.group & VTGroup.VOID:
            raise ValueError(
                f"ValueType {self} is of type {self.group}. "
                f"The signed flag should not be used on those groups."
            )
        self._signed = val

    @property
    def bit_width(self):
        if self.group & VTGroup.EXTERNAL or self.group & VTGroup.VOID:
            raise ValueError(
                f"ValueType {self} is of type {self.group}. "
                f"bit_width should not be used on those groups."
            )
        return self._bit_width

    @bit_width.setter
    def bit_width(self, val):
        if self.group & VTGroup.EXTERNAL or self.group & VTGroup.VOID:
            raise ValueError(
                f"ValueType {self} is of type {self.group}. "
                f"The signed flag should not be used on those groups."
            )
        self._bit_width = val

    def il_op(self, value: int):
        """Returns the corresponding SN/UN(size, val) string."""
        s = "SN" if self.signed else "UN"
        s += f"({self.bit_width}, {value:#x})"
        return s

    def get_param_decl_type(self) -> str:
        """Returns the type used for parameters."""
        if self.group & VTGroup.EXTERNAL or self.group & VTGroup.VOID:
            return self.external_type
        elif self.group & VTGroup.PURE:
            return "RZ_BORROW RzILOpPure *"
        raise ValueError(f"{self.group} not handled.")

    def __eq__(self, other):
        basics_match = self.bit_width == other.bit_width and self.signed == other.signed
        if self.group & (VTGroup.FLOAT | VTGroup.DOUBLE):
            return basics_match and self.format == other.format
        return basics_match

    def __gt__(self, other):
        return self.bit_width > other.bit_width

    def __lt__(self, other):
        return self.bit_width < other.bit_width

    def __ge__(self, other):
        return self.bit_width >= other.bit_width

    def __le__(self, other):
        return self.bit_width <= other.bit_width

    def __str__(self):
        if self.group & VTGroup.EXTERNAL:
            return f"EXTERNAL::{self.external_type}"
        elif self.group & VTGroup.VOID:
            return "void"
        return f'{"st" if self.signed else "ut"}{self.bit_width}'


def split_var_decl(decl: str) -> tuple[str, str]:
    """
    Splits a variable declaration of the form '<type> <name>' into its two parts.

    :param decl: The variable declaration.
    :return: A tuple with the type string at index 0 and the var name at index 1.
    """
    decl = decl.strip()
    matches = re.search(r"(?P<type>(\s*\w+[ *]+)+)\s*(?P<name>\w+$)", decl)
    return matches.group("type").strip(), matches.group("name").strip()


def get_value_type_by_c_type(type_id: str) -> ValueType:
    """
    Returns a value type for C type identifiers.

    :param type_id: The type identifier.
    :return: The Value type it correspond.
    """
    if type_id == "int":
        return ValueType(True, 32)
    elif type_id == "unsigned":
        return ValueType(False, 32)
    elif type_id == "float":
        return ValueType(
            True, 32, VTGroup.FLOAT | VTGroup.IEEE, format=FloatFormat.IEEE754_BIN_32
        )
    elif type_id == "double":
        return ValueType(
            True, 64, VTGroup.FLOAT | VTGroup.IEEE, format=FloatFormat.IEEE754_BIN_64
        )
    elif any([t in type_id for t in VTGroup.get_external_types()]):
        return ValueType(False, 64, VTGroup.EXTERNAL, type_id)
    elif type_id == "void":
        return ValueType(False, 32, VTGroup.VOID)

    if type_id.startswith("size"):
        type_match = re.search(r"size(?P<width>\d+)(?P<sign>[us])_t", type_id)
    else:
        type_match = re.search(r"(?P<sign>u?)int(?P<width>\d+)_t", type_id)
    if not type_match or len(type_match.groups()) != 2:
        raise ValueError(f"Types of the form {type_id} can't be parsed yet. If it is an external type,"
                         f"add it to get_external_types()")

    is_signed = False if type_match["sign"] == "u" else True
    width = int(type_match["width"])
    if type_id.startswith("size"):
        # Size has width in bytes
        width *= 8
    return ValueType(is_signed, width)


def get_smalles_val_type_for_number(num: int) -> int:
    if num & 0xFFFFFFFFFFFFFF00 == 0:
        size = 8
    elif num & 0xFFFFFFFFFFFF0000 == 0:
        size = 16
    elif num & 0xFFFFFFFF00000000 == 0:
        size = 32
    else:
        size = 64
    return size


def exc_if_types_not_match(a: ValueType, b: ValueType):
    if a != b:
        raise ValueError(
            "Value types don't match.\n"
            f"a size: {a.bit_width} signed: {a.signed}\n"
            f"b size: {b.bit_width} signed: {b.signed}"
        )


def c11_cast(a: ValueType, b: ValueType) -> tuple[ValueType, ValueType]:
    """Compares both value types against each other and converts them according to
    Chapter 6.3.1.8 of ISO/IEC 9899:201x (C11 Standard).
    Please note that we do not follow the rank definition from the standard.
    Here: Rank = width of type. Which should be close enough.
    """

    sign_match = a.signed == b.signed
    rank_match = a.bit_width == b.bit_width
    if sign_match and rank_match:
        return a, b
    va = deepcopy(a)
    vb = deepcopy(b)

    if sign_match:
        if va.bit_width < vb.bit_width:
            va.bit_width = vb.bit_width
        else:
            vb.bit_width = va.bit_width
        return va, vb

    a_is_signed = va.signed
    unsigned = vb if a_is_signed else va
    signed = va if a_is_signed else vb

    if unsigned.bit_width >= signed.bit_width:
        signed.bit_width = unsigned.bit_width
        signed.signed = False
    else:
        unsigned.bit_width = signed.bit_width
        unsigned.signed = True
    return (signed, unsigned) if a_is_signed else (unsigned, signed)


def get_value_type_from_reg_type(token_list: list) -> ValueType:
    """Determines the size for Hexagon registers by their parse tree tokens."""
    reg_type: Token = token_list[0].value  # R, P, V, Q etc.
    reg_access = token_list[1].type  # SRC/DEST/DEST_PAIR etc.

    if reg_type in ["R", "C", "M", "N"]:
        size = 32
    elif reg_type == "P":
        size = 8
    elif reg_type == "V":
        size = 1024
    elif reg_type == "Q":
        size = 128
    else:
        raise NotImplementedError(f"Register of reg type {reg_type} not handled.")

    if "PAIR" in reg_access:
        size *= 2
    # Register content is signed by default (see QEMUs tcg functions generating scripts).
    return ValueType(True, size)


def get_c_type_by_value_type(val_type: ValueType) -> str:
    """Returns the value type for the given C integer type."""

    res = ""
    if val_type.signed:
        res += "uint"
    else:
        res += "int"
    res += str(val_type.bit_width) + "_t"
    return res


def get_value_type_by_c_number(items: [Token]) -> ValueType:
    """Returns the value type for a list of parser tree tokens of a number."""
    try:
        val = int(items[0], get_num_base_by_token(items[0]))
    except Exception as e:
        raise NotImplementedError(f"Can not determine number format:\n{e}")

    postfix = items[1] if items[1] else ""

    c_signed_types_postfix = ["LL"]
    c_unsigned_types_postfix = ["ULL", "U"]
    c_64bit_postfix = ["LL", "ULL"]

    postfix = postfix.upper()
    if postfix != "" and (
        postfix not in c_signed_types_postfix
        and postfix not in c_unsigned_types_postfix
    ):
        raise NotImplementedError(f"Unsupported number postfix {postfix}")

    signed = True
    if postfix in c_unsigned_types_postfix:
        signed = False

    size = 32
    if postfix in c_64bit_postfix:
        size = 64
    return ValueType(signed, size)


def get_value_type_by_isa_imm(items: Token) -> ValueType:
    """Returns the value type for an immediate parser tree token."""

    imm_char = items[0]
    signed = False
    if re.search(r"[rRsS]", imm_char):
        signed = True

    # Immediate size is not encoded in the short code.
    return ValueType(signed, 32)
