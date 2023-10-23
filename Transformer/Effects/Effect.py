# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import Enum

from rzil_compiler.Transformer.TextCoord import TextCoord
from rzil_compiler.Exceptions import OverloadException
from rzil_compiler.Transformer.Pures.PureExec import PureExec


class EffectType(Enum):
    SETG = 0
    SETL = 1
    SET = 2  # Hybrids are SETG and SETL
    STOREW = 3
    STORE = 4
    JUMP = 5
    NOP = 6
    LOOP = 7
    SEQUENCE = 8
    EMPTY = 9
    BRANCH = 10


class Effect:
    name: str = ""
    type: EffectType = None
    effect_ops: list = None
    num_id = -1

    def __init__(self, name: str, effect_type: EffectType):
        self.text_coord = TextCoord()
        self.is_stmt = False  # Flag for fbody generation if this is a statement in C.

        self.name = name
        self.type = effect_type

    def __getattr__(self, name):
        match name:
            case "start_pos":
                return self.text_coord.start_pos
            case "end_pos":
                return self.text_coord.end_pos
            case "len":
                return self.text_coord.len
            case _:
                raise AttributeError(f"Attribute {name} does not exist.")

    def set_num_id(self, num_id: int):
        self.num_id = num_id

    def set_name(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name

    def il_write(self) -> str:
        """Returns the RZIL ops to write the variable value.
        :return: RZIL ops to write the pure value.
        """
        raise OverloadException("")

    def il_init_var(self) -> str:
        return f"RzILOpEffect *{self.effect_var()} = {self.il_write()};"

    def effect_var(self) -> str:
        """Returns the C variable name which holds the IL effect."""
        return self.get_name()

    def get_op_list(self):
        """Returns all Global, Local and LetPure operands this effect depends on as list."""
        from rzil_compiler.Transformer.Hybrids.Hybrid import Hybrid

        def get_ops(x):
            if isinstance(x, PureExec):
                ops = x.ops
            elif isinstance(x, Hybrid):
                ops = x.ops
            elif isinstance(x, Effect):
                return x.get_op_list()
            else:
                return x
            return [get_ops(y) for y in ops]

        from rzil_compiler.Transformer.helper import flatten_list

        return flatten_list([get_ops(o) for o in self.effect_ops])
