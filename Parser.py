# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from multiprocessing import Pool

from lark import Lark, Tree
from tqdm import tqdm

from Configuration import Conf, InputFile


class InsnParsingBundle:
    def __init__(self, grammar: str, name: str, behavior: list[str]):
        self.grammar = grammar
        self.name = name
        self.behavior = behavior


class ParserException:
    """
    multithreading needs pickable objects,
    which is not the case for the exceptions thrown by the parser.
    So we use this.
    """

    def __init__(self, exception: Exception):
        self.name = str(type(exception).__name__)


class ParsedInsn:
    def __init__(self, name: str, asts: list[Tree], behaviors: list[str], exception: ParserException | None = None):
        self.name = name
        self.asts: list = asts
        self.behaviors: list = behaviors
        self.exception = exception


def parse_single(bundle: InsnParsingBundle) -> dict[str: ParsedInsn]:
    name = bundle.name
    behaviors = bundle.behavior
    grammar = bundle.grammar
    parser = Lark(grammar, start="fbody", parser="earley", propagate_positions=True)
    try:
        asts = list()
        for b in behaviors:
            asts.append(parser.parse(b))
        pinsn = ParsedInsn(name, asts, behaviors)
    except Exception as e:
        pinsn = ParsedInsn(name, [], behaviors, ParserException(e))
    return {name: pinsn}


class Parser:
    def __init__(self):
        pass

    @staticmethod
    def parse(insn_behavior: dict[str, list]) -> dict[str, ParsedInsn]:
        with open(Conf.get_path(InputFile.GRAMMAR, "Hexagon")) as f:
            grammar = "".join(f.readlines())

        args = [
            InsnParsingBundle(grammar, insn_name, insn_beh)
            for insn_name, insn_beh in insn_behavior.items()
        ]
        result: dict[str, ParsedInsn] = dict()
        with Pool() as pool:
            for res in tqdm(
                pool.imap(parse_single, args), total=len(args), desc="Parse shortcode"
            ):
                result.update(res)
        return result
