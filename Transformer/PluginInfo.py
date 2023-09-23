# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

hexagon_c_call_prefix = "HEX_"
hexagon_isa_to_reg = "ISA2REG"
hexagon_isa_to_reg_args = ["hi"]
hexagon_isa_to_imm = "ISA2IMM"
hexagon_isa_to_imm_args = ["hi"]
hexagon_isa_alias_to_op = "ALIAS2OP"
hexagon_isa_alias_to_op_args = []
hexagon_isa_explicit_to_op = "EXPLICIT2OP"
hexagon_isa_explicit_to_op_args = []
# This function gets a register placeholder name from the ISA manual (e.g. "Rs")
# and returns the actual register name as string (e.g. "R3")
isa_to_reg_fnc = hexagon_isa_to_reg
# Arguments the function gets.
isa_to_reg_args = hexagon_isa_to_reg_args
isa_alias_to_op = hexagon_isa_alias_to_op
isa_alias_to_op_args = hexagon_isa_alias_to_op_args
isa_explicit_to_op = hexagon_isa_explicit_to_op
isa_explicit_to_op_args = hexagon_isa_explicit_to_op_args

# This function gets an immediate placeholder name from the ISA manual (e.g. uiV) and returns
# an initialized RZIL Pure with the correct size (e.g. UN(9, 0x10)
isa_to_imm_fnc = hexagon_isa_to_imm
isa_to_imm_args = hexagon_isa_to_imm_args
