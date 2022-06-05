# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from lark import Token

from Exceptions import OverloadException


class TransformerExtension:

    def reg(self, items: [Token]):
        raise OverloadException('Overload this method to parse register tokens.')

    def imm(self, items: [Token]):
        raise OverloadException('Overload this method to parse immediate tokens.')

    def get_value_type_by_resource_type(self, t):
        raise OverloadException('Overload this method to convert types from the resources to ValueTypes.')

    def set_token_meta_data(self, token_name: str):
        raise OverloadException('Overload this method to set certain meta data if a token is transformed.')

    def get_meta(self):
        raise OverloadException('Overload this method to return the meta data of this instruction.')
