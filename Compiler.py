#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import argparse
import sys
import traceback

from lark import UnexpectedToken, UnexpectedCharacters, UnexpectedEOF
from lark.exceptions import VisitError
from lark.lark import Lark
from tqdm import tqdm

from ArchEnum import ArchEnum
from Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
from Transformer.RZILTransformer import RZILTransformer


class Compiler:
    preprocessor = None
    parser = None
    transformer = None
    compiled_insns = dict()

    def __init__(self, arch: ArchEnum, path_resources: str):
        self.arch: ArchEnum = arch
        self.path_resources: str = path_resources

        self.set_parser()
        self.set_transformer()
        self.set_preprocessor()

    def set_parser(self):
        print("* Set up Lark parser.")
        with open(self.path_resources + "/grammar.lark") as f:
            grammar = "".join(f.readlines())

        self.parser = Lark(grammar, start="fbody", parser="lalr")

    def set_transformer(self):
        self.transformer = RZILTransformer(self.arch)

    def set_preprocessor(self):
        print(f"* Set up preprocessor for: {self.arch.name}")
        if self.arch == ArchEnum.HEXAGON:
            shortcode = self.path_resources + "/Preprocessor/shortcode.h"
            macros = {
                'standard': self.path_resources + "/Preprocessor/macros.h",
                'vec': self.path_resources + "/Preprocessor/macros_mmvec.h",
                'patches': self.path_resources + "/Preprocessor/macro_patches.h",
            }
            out_dir = self.path_resources
            self.preprocessor = PreprocessorHexagon(shortcode, macros, out_dir)
        else:
            raise NotImplementedError(f"Preprocessor for arch: {self.arch.name} not known.")

    def run_preprocessor(self):
        print("* Run preprocessor...")
        self.preprocessor.run_preprocess_steps()

    def test_compile_all(self):
        print("* Test: Compile all instructions.")
        keys = ["no_term", "no_char", "eof", "visit", "other", "ok"]
        stats = {k: {"count": 0} for k in keys}
        excs = dict()

        for insn in tqdm(self.preprocessor.behaviors.keys(), desc="Compiling..."):
            e = None
            try:
                self.compile_insn(insn)
                exc_name = "ok"
            except UnexpectedToken as x:
                # Parser got unexpected token
                exc_name = "no_term"
                e = x
            except UnexpectedCharacters as x:
                # Lexer can not match character to token.
                exc_name = "no_char"
                e = x
            except UnexpectedEOF as x:
                # Parser expected a token but got EOF
                exc_name = "eof"
                e = x
            except VisitError as x:
                # Something went wrong in the transformer
                exc_name = "visit"
                e = x
            except Exception as x:
                exc_name = "other"
                e = x

            stats[exc_name]["count"] += 1
            if e:
                e_name = type(e).__name__
                tup = (insn, self.preprocessor.get_insn_behavior(insn), e)
                if e_name in excs:
                    excs[e_name].append(tup)
                else:
                    excs[e_name] = [tup]

        for k, v in stats.items():
            print(f'{k} = {v["count"]}')

        self.fix_compile_exceptions(excs)

    @staticmethod
    def fix_compile_exceptions(exceptions: dict):
        for i, k in enumerate(exceptions.keys()):
            print(f"[{i}] {k}")
        i = 0
        while True:
            inp = input("Choose exception type print (number or q: quit)\n > ")
            if inp == 'q':
                exit()
            try:
                i = int(inp)
                break
            except ValueError:
                continue
        for k, e in enumerate(exceptions.keys()):
            if k != i:
                continue
            h = 0
            while h != len(exceptions[e]):
                insn: str = exceptions[e][h][0]
                beh: str = exceptions[e][h][1]
                ex = exceptions[e][h][2]
                print(f"INSTRUCTION: {insn}\n\nBEHAVIOR: \n{beh}\n\nEXCEPTION: {type(ex)} : {ex}\n")
                print(f"TRACE: \n{traceback.print_tb(ex.__traceback__)}")
                if isinstance(ex, VisitError):
                    print(f"ORIGINAL EXCEPTION: {ex.orig_exc}\n")
                    print(f"TRACE:\n{traceback.print_tb(ex.orig_exc.__traceback__)}")
                cmd = input("\n[n = next, q = quit] > ")
                if cmd == "n":
                    h += 1
                elif cmd == "q":
                    exit()

    def compile_insn(self, insn_name: str) -> [str]:
        """ Compiles the instruction <insn_name> and returns the RZIL code.
            An instruction of certain architectures can have multiple behaviors,
            so this method returns a list of compiled behaviors.
            For most instructions this list has a length of 1.
        """
        behaviors = self.preprocessor.get_insn_behavior(insn_name)
        if not behaviors:
            raise NotImplementedError(f"Behavior for instruction {insn_name} not known by the preprocessor.")

        parse_trees = [self.parser.parse(behavior) for behavior in behaviors]
        self.compiled_insns[insn_name]['rzil'] = []
        self.compiled_insns[insn_name]['meta'] = []
        for pt in parse_trees:
            self.compiled_insns[insn_name]['rzil'].append(self.transformer.transform(pt))
            self.compiled_insns[insn_name]['meta'].append(self.transformer.ext.get_meta())

        return self.compiled_insns[insn_name]

    def get_insn_rzil(self, insn_name: str) -> [str]:
        if insn_name in self.compiled_insns:
            return self.compiled_insns[insn_name]['behavior']
        raise ValueError(f'Instruction {insn_name} not found.')

    def get_insn_meta(self, insn_name: str) -> str:
        if insn_name in self.compiled_insns:
            return self.compiled_insns[insn_name]['meta']
        raise ValueError(f'Instruction {insn_name} not found.')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.argv += ["--help"]

    argp = argparse.ArgumentParser(
        prog="RZIL Compiler", description="Compiles RZIL instructions from varies architectures."
    )
    argp.add_argument(
        "-r",
        dest="resources",
        metavar="path",
        required=False,
        help='Path to resources. Defaults to: "./Resources/<Arch name>"',
    )
    argp.add_argument("-a", dest="arch", choices=["Hexagon"], required=True, help="Architecture to compile for.")
    argp.add_argument(
        "-t",
        dest="test_all",
        action="store_true",
        help="Try to compile all instructions from the resources and print a statistic about it.",
    )
    argp.add_argument("-s", dest="skip_pp", action="store_true", help="Skip file processing steps of the preprocessor.")

    args = argp.parse_args(sys.argv[1:])
    res_path = f"./Resources/{args.arch}/" if not args.resources else args.resources
    c = Compiler(ArchEnum[args.arch.upper()], res_path)
    if not args.skip_pp:
        c.run_preprocessor()
    c.preprocessor.load_insn_behavior()

    if args.test_all:
        c.test_compile_all()
        # c.test_euclid()
        exit()
