#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only
import argparse
import sys
import traceback
from enum import Enum

from lark import UnexpectedToken, UnexpectedCharacters, UnexpectedEOF
from lark.exceptions import VisitError
from lark.lark import Lark
from tqdm import tqdm

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

        self.set_parser()
        self.set_transformer()
        self.set_preprocessor()

    def set_parser(self):
        print("* Set up Lark parser.")
        with open(self.path_resources + "/grammar.lark") as f:
            grammar = "".join(f.readlines())

        self.parser = Lark(grammar, start="fbody", parser="lalr")

    def set_transformer(self):
        self.transformer = RZILTransformer()

    def set_preprocessor(self):
        print(f"* Set up preprocessor for: {self.arch.name}")
        if self.arch == ArchEnum.HEXAGON:
            shortcode = self.path_resources + "/Preprocessor/shortcode.h"
            macros = [
                self.path_resources + "/Preprocessor/macros.h",
                self.path_resources + "/Preprocessor/mmve_macros.h",
            ]
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
        i = int(input("Choose exception type print\n > "))
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

    def compile_insn(self, insn_name: str):
        behavior = self.preprocessor.get_insn_behavior(insn_name)
        if not behavior:
            raise NotImplementedError(f"Behavior for instruction {insn_name} not known by the preprocessor.")

        parse_tree = self.parser.parse(behavior)
        return self.transformer.transform(parse_tree)


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
        # c.test_compile_all()
        c.test_euclid()
        exit()
