# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from Exceptions import OverloadException


class CompilerExtension:

    def transform_insn_name(self, insn_name: str) -> str:
        raise OverloadException('Please overload this method.')
