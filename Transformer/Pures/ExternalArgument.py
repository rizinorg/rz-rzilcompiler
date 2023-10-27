# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Transformer.ValueType import ValueType, VTGroup


class ExternalArgument:
    """
    This Argument is just a wrapper class around arguments with an external type.
    Those are simple strings and have only a meaning in the C world.

    Since we can not pass just strings as arguments to sub-routines or macros
    (they require a get_op_val() method).
    """

    def __init__(self, identifier: str, v_type: ValueType):
        self.identifier = identifier
        self.v_type: ValueType = v_type

    def get_op_var(self) -> str:
        return self.identifier

    def __str__(self):
        return self.identifier


RZ_FLOAT_IEEE754_BIN_32_ARG = ExternalArgument(
    "RZ_FLOAT_IEEE754_BIN_32", ValueType(True, 32, VTGroup.EXTERNAL, "RzFloatFormat")
)
RZ_FLOAT_IEEE754_BIN_64_ARG = ExternalArgument(
    "RZ_FLOAT_IEEE754_BIN_64", ValueType(True, 64, VTGroup.EXTERNAL, "RzFloatFormat")
)
