#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import argparse
from time import sleep

from lark.exceptions import VisitError
from tqdm import tqdm

from rzil_compiler.Parser import Parser, ParserException
from rzil_compiler.ArchEnum import ArchEnum
from rzil_compiler.Configuration import Conf, InputFile
from rzil_compiler.Helper import log
from rzil_compiler.HexagonExtensions import HexagonCompilerExtension
from rzil_compiler.Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
from rzil_compiler.Transformer.RZILTransformer import RZILTransformer


class Compiler:
    preprocessor = None
    parser = None
    transformer = None
    compiled_insns = dict()
    asts = dict()  # Abstract syntax trees
    ext = None

    def __init__(self, arch: ArchEnum):
        self.arch: ArchEnum = arch

        self.set_extension()
        self.set_transformer()
        self.set_preprocessor()

    def set_extension(self):
        if self.arch == ArchEnum.HEXAGON:
            self.ext = HexagonCompilerExtension()
        else:
            raise NotImplementedError(f"No compiler extension for {self.arch} given.")

    def set_transformer(self):
        self.transformer = RZILTransformer(self.arch)

    def set_preprocessor(self):
        log(f"Set up preprocessor for: {self.arch.name}")
        if self.arch == ArchEnum.HEXAGON:
            shortcode = Conf.get_path(InputFile.HEXAGON_PP_SHORTCODE_H)
            self.preprocessor = PreprocessorHexagon(shortcode)
        else:
            raise NotImplementedError(
                f"Preprocessor for arch: {self.arch.name} not known."
            )

    def run_preprocessor(self):
        log("Run preprocessor...")
        self.preprocessor.run_preprocess_steps()

    def test_compile_all(self):
        self.parse_shortcode()

        keys = [
            "Successful",
            "UnexpectedToken",
            "UnexpectedCharacters",
            "UnexpectedEOF",
            "VisitError",
            "Exception",
        ]
        stats = {k: {"count": 0} for k in keys}

        log("Transform ASTs...")
        for insn_name, trees in tqdm(self.asts.items()):
            if isinstance(trees[0], ParserException):
                match trees[0].name:
                    case "UnexpectedToken":
                        # Parser got unexpected token
                        exc_name = "UnexpectedToken"
                    case "UnexpectedCharacters":
                        # Lexer can not match character to token.
                        exc_name = "UnexpectedCharacters"
                    case "UnexpectedEOF":
                        exc_name = "UnexpectedEOF"
                    case "Exception" | _:
                        exc_name = "Exception"
            else:
                try:
                    self.transform_insn(insn_name, trees)
                    exc_name = "Successful"
                except VisitError:
                    # Something went wrong in the transformer
                    exc_name = "VisitError"
                except Exception:
                    exc_name = "Exception"

            stats[exc_name]["count"] += 1

        if sum([stats[k]["count"] for k in stats.keys() if k != "Successful"]) == 0:
            log("All instructions compiled successfully!")
            return

        log("Results:")
        for k, v in stats.items():
            print(f'\t{k} = {v["count"]}')

    def compile_insn(self, insn_name: str) -> [str]:
        return self.transform_insn(insn_name, self.asts[insn_name])

    def parse_shortcode(self):
        log("Parse shortcode...")
        self.asts = Parser().parse(self.preprocessor.behaviors)

    def transform_insn(self, insn_name: str, parse_trees: list) -> [str]:
        """Compiles the instruction <insn_name> and returns the RZIL code.
        An instruction of certain architectures can have multiple behaviors,
        so this method returns a list of compiled behaviors.
        For most instructions this list has a length of 1.
        """
        try:
            insn = self.ext.transform_insn_name(insn_name)
            self.compiled_insns[insn] = {"rzil": [], "meta": [], "parse_trees": []}
            for pt in parse_trees:
                self.transformer.reset()
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
        description="Compiles RZIL instructions from various architectures.",
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
