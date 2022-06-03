#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import argparse
import sys
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
        print('* Set up Lark parser.')
        with open(self.path_resources + '/grammar.lark') as f:
            grammar = ''.join(f.readlines())

        self.parser = Lark(grammar, start="fbody")

    def set_transformer(self):
        self.transformer = RZILTransformer()

    def set_preprocessor(self):
        print(f'* Set up preprocessor for: {self.arch.name}')
        if self.arch == ArchEnum.HEXAGON:
            shortcode = self.path_resources + '/Preprocessor/shortcode.h'
            macros = [self.path_resources + '/Preprocessor/macros.h',
                      self.path_resources + '/Preprocessor/mmve_macros.h']
            out_dir = self.path_resources
            self.preprocessor = PreprocessorHexagon(shortcode, macros, out_dir)
        else:
            raise NotImplemented(f'Preprocessor for arch: {self.arch.name} not known.')

    def run_preprocessor(self):
        print('* Run preprocessor...')
        self.preprocessor.run_preprocess_steps()
        self.preprocessor.load_insn_behavior()

    def compile_insn(self, insn_name: str):
        behavior = self.preprocessor.get_insn_behavior(insn_name)
        if not behavior:
            raise NotImplemented(f'Behavior for instruction {insn_name} not known by the preprocessor.')
        parse_tree = self.parser.parse(behavior)
        return self.transformer.transform(parse_tree)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.argv += ['--help']

    argp = argparse.ArgumentParser(
        prog='RZIL Compiler',
        description='Compiles RZIL instructions from varies architectures.')
    argp.add_argument('-r', dest='resources', metavar='path', required=False,
                      help='Path to resources. Defaults to: "./Resources/<Arch name>"')
    argp.add_argument('-a', dest='arch', choices=['Hexagon'], required=True, help='Architecture to compile for.')

    args = argp.parse_args(sys.argv[1:])
    res_path = f'./Resources/{args.arch}/' if not args.resources else args.resources
    c = Compiler(ArchEnum[args.arch.upper()], res_path)
    c.set_parser()
    c.set_preprocessor()
    c.run_preprocessor()
