#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import argparse
import json
import re

from lark import Lark
from lark.exceptions import VisitError
from tqdm import tqdm

from helperFunctions import LogLevel
from rzil_compiler.Transformer.ValueType import get_value_type_by_c_type, split_var_decl
from rzil_compiler.Transformer.Pures.Parameter import Parameter
from rzil_compiler.Transformer.Hybrids.SubRoutine import SubRoutine
from rzil_compiler.Parser import Parser, ParserException
from rzil_compiler.ArchEnum import ArchEnum
from rzil_compiler.Configuration import Conf, InputFile
from rzil_compiler.Helper import log
from rzil_compiler.HexagonExtensions import HexagonCompilerExtension
from rzil_compiler.Preprocessor.Hexagon.PreprocessorHexagon import PreprocessorHexagon
from rzil_compiler.Transformer.RZILTransformer import RZILTransformer


class RZILInstruction:
    """Holds all the information about a transformed instruction."""

    def __init__(
        self,
        name: str,
        rzil: list[str],
        meta: list[list[str]],
        parse_trees: list[str],
        not_implemented=False,
    ):
        self.name = name
        self.not_implemented = not_implemented
        self.rzil = rzil

        self.needs_hi: list[bool] = list()
        self.needs_pkt: list[bool] = list()
        for i, code in enumerate(self.rzil):
            self.needs_hi.append(
                not self.not_implemented and re.search(r"\Whi\W", code)
            )
            self.needs_pkt.append(not self.not_implemented and "pkt" in code)

        self.meta = meta
        self.parse_trees = parse_trees
        self.getter_rzil = {"name": [], "fcn_decl": []}
        if len(self.rzil) == 1:
            # No _partX postfix for instructions with only one part
            self.getter_rzil["name"].append(self.gen_hex_il_op_getter_name(self.name))
            self.getter_rzil["fcn_decl"].append(
                self.gen_hex_il_op_getter_name(self.name, fcn_decl=True)
            )
        else:
            for i in range(len(self.rzil)):
                self.getter_rzil["name"].append(
                    self.gen_hex_il_op_getter_name(self.name, i)
                )
                self.getter_rzil["fcn_decl"].append(
                    self.gen_hex_il_op_getter_name(self.name, i, fcn_decl=True)
                )

        assert (
            len(self.rzil)
            == len(self.meta)
            == len(self.parse_trees)
            == len(self.getter_rzil["name"])
            == len(self.getter_rzil["fcn_decl"])
            == len(self.needs_pkt)
            == len(self.needs_hi)
        )

    @staticmethod
    def gen_hex_il_op_getter_name(
        insn_name: str, part: int = -1, fcn_decl: bool = False
    ) -> str:
        if part < 0:
            name = f"hex_il_op_{insn_name.lower()}"
        else:
            name = f"hex_il_op_{insn_name.lower()}_part{part}"
        if fcn_decl:
            return f"RzILOpEffect *{name}(HexInsnPktBundle *bundle)"
        return name

    @staticmethod
    def get_unimplemented_rzil_instr(instr_name: str):
        instr = RZILInstruction(
            instr_name,
            ["NOT_IMPLEMENTED;"],
            [["HEX_IL_INSN_ATTR_INVALID"]],
            [""],
            not_implemented=True,
        )
        return instr

    def __getitem__(self, item: str):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)


class Compiler:
    preprocessor = None
    parser = None  # Parser only used for single statement compilations. Instructions are compiled in Parser.py
    transformer = None
    compiled_insns = dict()
    asts = dict()  # Abstract syntax trees
    sub_routines: dict[
        str:SubRoutine
    ] = dict()  # dict of sub-routines which can be used by other instructions.
    ext = None

    def __init__(self, arch: ArchEnum, add_subroutines=True):
        self.arch: ArchEnum = arch

        self.set_lark_parser()
        self.set_extension()
        self.set_il_op_transformer()
        self.set_preprocessor()
        if add_subroutines:
            self.add_sub_routines()

    def set_lark_parser(self):
        with open(Conf.get_path(InputFile.GRAMMAR, "Hexagon")) as f:
            grammar = "".join(f.readlines())
        self.parser = Lark(
            grammar, start="fbody", parser="earley", propagate_positions=True
        )

    def set_extension(self):
        if self.arch == ArchEnum.HEXAGON:
            self.ext = HexagonCompilerExtension()
        else:
            raise NotImplementedError(f"No compiler extension for {self.arch} given.")

    def set_il_op_transformer(self):
        # pkt and hi are not actually passed to every function (they are passed via bundle).
        # But for now we just ignore this, because they'd need the "->" operator implemented to access them.
        params = [
            Parameter("pkt", get_value_type_by_c_type("HexPkt")),
            Parameter("hi", get_value_type_by_c_type("HexInsn")),
            Parameter("bundle", get_value_type_by_c_type("HexInsnPktBundle")),
        ]
        ret_type = get_value_type_by_c_type("RzILOpEffect")
        self.transformer = RZILTransformer(
            self.arch,
            sub_routines=self.sub_routines,
            parameters=params,
            return_type=ret_type,
        )

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

    def add_sub_routines(self):
        log("Add sub-routines...")
        with open(Conf.get_path(InputFile.HEXAGON_SUB_ROUTINES_JSON)) as f:
            routines = json.load(f)
        for name, routine in routines["sub_routines"].items():
            self.add_sub_routine(
                name, routine["return_type"], routine["params"], routine["code"]
            )

    def add_sub_routine(
        self, name: str, ret_type: str, params: list[str], body: str
    ) -> None:
        """
        Compiles a sub-routine and buffers it for later usage.
        :param name: The name of the sub_routine.
        :param ret_type: The return type in c syntax
        :param params: A list of parameters of this sub-routine in the form of "<type> <id>"
        :param body: The code of the sub-routines body.
        """
        sub_routine = self.compile_sub_routine(name, ret_type, params, body)
        self.sub_routines[name] = sub_routine
        self.transformer.update_sub_routines(self.sub_routines)
        log(f"Added sub-routine: {name}")

    def get_sub_routine(self, name: str) -> SubRoutine:
        return self.sub_routines[name]

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

    def compile_sub_routine(
        self, name: str, return_type: str, parameter: list[str], body: str
    ) -> SubRoutine:
        """
        Returns a SubRoutine object initialized with the given arguments.
        :param name: The name of the sub_routine.
        :param return_type: The return type in c syntax
        :param parameter: A list of parameters of this sub-routine in the form of "<type> <id>"
        :param body: The code of the sub-routines body.
        :return: The sub-routine object to initialization.
        """
        if name in self.sub_routines:
            log(f"Return already compiled sub-routine {name}")
            return self.sub_routines[name]

        params = list()
        for param in parameter:
            ptype, pname = split_var_decl(param)
            p = Parameter(pname, get_value_type_by_c_type(ptype))
            params.append(p)

        ret_type = get_value_type_by_c_type(return_type)
        # Compile the body
        ast_body = self.parser.parse(body)
        transformer = RZILTransformer(
            ArchEnum.HEXAGON,
            sub_routines=self.sub_routines,
            parameters=params,
            return_type=ret_type,
        )
        transformer.set_text(body)
        transformed_body = transformer.transform(ast_body)
        return SubRoutine(name, ret_type, params, transformed_body)

    def compile_c_stmt(self, code: str) -> str:
        """
        Compiles an arbitrary C statement to RzIL.
        Statement must be wrapped in curley brackets: "{ <code> }".

        :param code: The C code to compile.
        :return: The RzIL representation of it.
        """
        ast = self.parser.parse(code)
        self.transformer.set_text(code)
        result = self.transformer.transform(ast)
        self.transformer.reset()
        return result

    def compile_insn(self, insn_name: str) -> RZILInstruction:
        return self.transform_insn(insn_name, self.asts[insn_name])

    def parse_shortcode(self):
        log("Parse shortcode...")
        self.asts = Parser().parse(self.preprocessor.behaviors)

    def transform_insn(self, insn_name: str, parse_trees: list) -> RZILInstruction:
        """Compiles the instruction <insn_name> and returns the RZIL code.
        An instruction of certain architectures can have multiple behaviors,
        so this method returns a list of compiled behaviors.
        For most instructions this list has a length of 1.
        """
        try:
            insn = self.ext.transform_insn_name(insn_name)
            rzil = list()
            meta = list()
            trees = list()
            for pt in parse_trees:
                self.transformer.reset()
                self.transformer.set_text(pt.text)
                rzil.append(self.transformer.transform(pt))
                meta.append(self.transformer.ext.get_meta())
                trees.append(pt.pretty())
            self.compiled_insns[insn] = RZILInstruction(insn, rzil, meta, trees)
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
