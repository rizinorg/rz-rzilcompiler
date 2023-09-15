# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzil_compiler.Exceptions import OverloadException


class CompilerExtension:
    def transform_insn_name(self, insn_name: str) -> str:
        """Some instruction names possibly need to be transformed.
        For example if the program which invokes the compiler has different
        instruction names than the resources.
        E.g. dep_A2_tfs -> A2_tfs
        """
        raise OverloadException("Please overload this method.")
