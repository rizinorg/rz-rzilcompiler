#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import argparse
import traceback

from lark import UnexpectedToken, UnexpectedCharacters, UnexpectedEOF
from lark.exceptions import VisitError
from lark.lark import Lark
from tqdm import tqdm

from ArchEnum import ArchEnum
from Configuration import Conf, InputFile
from HexagonExtensions import HexagonCompilerExtension
from Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
from Transformer.ILOpsHolder import ILOpsHolder
from Transformer.RZILTransformer import RZILTransformer


class Compiler:
    preprocessor = None
    parser = None
    transformer = None
    compiled_insns = dict()
    ext = None

    def __init__(self, arch: ArchEnum):
        self.arch: ArchEnum = arch

        self.set_extension()
        self.set_parser()
        self.set_transformer()
        self.set_preprocessor()

    def set_extension(self):
        if self.arch == ArchEnum.HEXAGON:
            self.ext = HexagonCompilerExtension()
        else:
            raise NotImplementedError(f"No compiler extension for {self.arch} given.")

    def set_parser(self):
        print("* Set up Lark parser.")
        with open(Conf.get_path(InputFile.GRAMMAR, self.arch)) as f:
            grammar = "".join(f.readlines())

        self.parser = Lark(grammar, start="fbody", parser="earley")

    def set_transformer(self):
        self.transformer = RZILTransformer(self.arch)

    def set_preprocessor(self):
        print(f"* Set up preprocessor for: {self.arch.name}")
        if self.arch == ArchEnum.HEXAGON:
            shortcode = Conf.get_path(InputFile.HEXAGON_PP_SHORTCODE_H)
            macros = {
                "standard": Conf.get_path(InputFile.HEXAGON_PP_MACROS_H),
                "vec": Conf.get_path(InputFile.HEXAGON_PP_MACROS_MMVEC_H),
                "patches": Conf.get_path(InputFile.HEXAGON_PP_MACROS_PATCHES_H),
            }
            self.preprocessor = PreprocessorHexagon(shortcode, macros)
        else:
            raise NotImplementedError(
                f"Preprocessor for arch: {self.arch.name} not known."
            )

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
                behavior = self.preprocessor.get_insn_behavior(insn)
                try:
                    tree = self.parser.parse(behavior[0]).pretty()
                except Exception:
                    tree = "No tree present"
                tup = (insn, behavior, e, tree)
                if e_name in excs:
                    excs[e_name].append(tup)
                else:
                    excs[e_name] = [tup]

        if len(excs) == 0:
            print("* All instructions compiled successfully!")
            return

        for k, v in stats.items():
            print(f'{k} = {v["count"]}')
        stats = dict()
        for v_exc in excs["VisitError"]:
            err: VisitError = v_exc[2]
            exc_str = str(err.orig_exc)
            if exc_str in stats:
                stats[exc_str] += 1
            else:
                stats[exc_str] = 1
        print("Visit Errors:")
        for k, x in stats.items():
            print(f"\t{x} - {k}")

        self.fix_compile_exceptions(excs)

    @staticmethod
    def fix_compile_exceptions(exceptions: dict):
        for i, k in enumerate(exceptions.keys()):
            print(f"[{i}] {k}")
        i = 0
        while True:
            inp = input("Choose exception type print (number or q: quit)\n > ")
            if inp == "q":
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
                tree = exceptions[e][h][3]
                print(f"\nTree: {tree}\n")
                print(f"EXCEPTION: {type(ex)} : {ex}\n")
                print(f"TRACE: \n{traceback.print_tb(ex.__traceback__)}")
                if isinstance(ex, VisitError):
                    print(f"ORIGINAL EXCEPTION: {ex.orig_exc}\n")
                    print(f"TRACE:\n{traceback.print_tb(ex.orig_exc.__traceback__)}")
                print(f"INSTRUCTION: {insn}\n\nBEHAVIOR: \n{beh}\n")
                cmd = input("\n[n = next, b = back, q = quit] > ")
                if cmd == "n":
                    h += 1
                elif cmd == "q":
                    exit()
                elif cmd == "b":
                    Compiler.fix_compile_exceptions(exceptions)

    def compile_insn(self, insn_name: str) -> [str]:
        """Compiles the instruction <insn_name> and returns the RZIL code.
        An instruction of certain architectures can have multiple behaviors,
        so this method returns a list of compiled behaviors.
        For most instructions this list has a length of 1.
        """
        try:
            insn = self.ext.transform_insn_name(insn_name)
            behaviors = self.preprocessor.get_insn_behavior(insn)
            if not behaviors:
                raise NotImplementedError(
                    f"Behavior for instruction {insn_name} not known by the preprocessor."
                )

            parse_trees = [self.parser.parse(behavior) for behavior in behaviors]
            self.compiled_insns[insn] = {"rzil": [], "meta": [], "parse_trees": []}
            for pt in parse_trees:
                self.transformer.reset()
                ILOpsHolder().clear()
                self.compiled_insns[insn]["rzil"].append(self.transformer.transform(pt))
                self.compiled_insns[insn]["meta"].append(
                    self.transformer.ext.get_meta()
                )
                self.compiled_insns[insn]["parse_trees"].append(pt.pretty())
            return self.compiled_insns[insn]
        except Exception as e:
            raise e
        finally:
            self.transformer.reset()
            ILOpsHolder().clear()

    def get_insn_rzil(self, insn_name: str) -> [str]:
        if insn_name in self.compiled_insns:
            return self.compiled_insns[insn_name]["behavior"]
        raise ValueError(f"Instruction {insn_name} not found.")

    def get_insn_meta(self, insn_name: str) -> str:
        if insn_name in self.compiled_insns:
            return self.compiled_insns[insn_name]["meta"]
        raise ValueError(f"Instruction {insn_name} not found.")


def parse_args() -> argparse.Namespace:
    argp = argparse.ArgumentParser(
        prog="RZIL Compiler",
        description="Compiles RZIL instructions from varies architectures.",
    )
    argp.add_argument(
        "-a",
        dest="arch",
        choices=["Hexagon"],
        required=True,
        help="Architecture to compile for.",
    )
    argp.add_argument(
        "-t",
        dest="test_all",
        action="store_true",
        help="Try to compile all instructions from the resources and print a statistic about it.",
    )
    argp.add_argument(
        "-s",
        dest="skip_pp",
        action="store_true",
        help="Skip file processing steps of the preprocessor.",
    )
    return argp.parse_args()


if __name__ == "__main__":
    args = parse_args()
    c = Compiler(ArchEnum[args.arch.upper()])
    if not args.skip_pp:
        c.run_preprocessor()
    c.preprocessor.load_insn_behavior()

    if args.test_all:
        c.test_compile_all()
