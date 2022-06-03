# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import os
from enum import Enum

from lark.lark import Lark

from Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
from Transformer.RZILTransformer import RZILTransformer


class ArchEnum(Enum):
    HEXAGON = 0


class Compiler:
    preprocessor = None
    parser = None
    transformer = None

    def __init__(self, arch: ArchEnum, path_resources: str):
        self.arch: ArchEnum = arch
        self.path_resources: str = path_resources

    def set_parser(self):
        with open(self.path_resources + '/grammar.lark') as f:
            grammar = ''.join(f.readlines())

        self.parser = Lark(grammar, start="fbody")

    def set_transformer(self):
        self.transformer = RZILTransformer()

    def set_preprocessor(self):
        if self.arch == ArchEnum.HEXAGON:
            shortcode = self.path_resources + '/Preprocessor/shortcode.h'
            macros = [self.path_resources + '/Preprocessor/macros.h',
                      self.path_resources + '/Preprocessor/mmve_macros.h']
            out_dir = self.path_resources
            self.preprocessor = PreprocessorHexagon(shortcode, macros, out_dir)
            self.preprocessor.load_insn_behavior()
        else:
            raise NotImplemented(f'Preprocessor for arch: {self.arch.name} not known.')

    def run_preprocessor(self):
        pass

    def compile_insn(self, insn_name: str):
        behavior = self.preprocessor.get_insn_behavior(insn_name)
        if not behavior:
            raise NotImplemented(f'Behavior for instruction {insn_name} not known by the preprocessor.')
        parse_tree = self.parser.parse(behavior)
        return self.transformer.transform(parse_tree)


if __name__ == '__main__':
    c = Compiler(ArchEnum.HEXAGON, '/home/user/repos/rzil-hexagon/Resources/Hexagon/')
    c.set_parser()
    c.set_preprocessor()
