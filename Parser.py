# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from multiprocessing import Pool

from lark import Lark
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


def parse_single(bundle: InsnParsingBundle) -> dict[str, list]:
    name = bundle.name
    behavior = bundle.behavior
    grammar = bundle.grammar
    result = dict()
    result[name] = list()
    parser = Lark(grammar, start="fbody", parser="earley", propagate_positions=True)
    try:
        for b in behavior:
            ast = parser.parse(b)
            result[name].append(ast)
    except Exception as e:
        result[name].append(ParserException(e))
    return result


class Parser:
    def __init__(self):
        pass

    @staticmethod
    def parse(insn_behavior: dict[str, list]):
        with open(Conf.get_path(InputFile.GRAMMAR, "Hexagon")) as f:
            grammar = "".join(f.readlines())

        args = [
            InsnParsingBundle(grammar, insn_name, insn_beh)
            for insn_name, insn_beh in insn_behavior.items()
        ]
        result = dict()
        with Pool() as pool:
            for res in tqdm(
                pool.imap(parse_single, args), total=len(args), desc="Parse shortcode"
            ):
                result.update(res)
        return result
