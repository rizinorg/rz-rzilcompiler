#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import re
import pcpp


class PreprocessorHexagon:

    behaviors = dict()  # dict(ID : Behavior)

    def __init__(self, shortcode_path: str, macros_paths: [str], out_dir: str):
        self.shortcode_path = shortcode_path
        self.macros_paths = macros_paths
        self.out_dir = out_dir

    def run_preprocess_steps(self):
        self.preprocess_macros()
        self.preprocess_shortcode()

    def preprocess_macros(self):
        """ Remove includes. Decide between QEMU_GENERATE or not. """
        pass

    def preprocess_shortcode(self):
        """ Run pcpp on shortcode + macro files. """
        combined_path = self.out_dir + '/Preprocessor/combined.h'
        with open(combined_path, 'w') as f:
            for path in self.macros_paths + [self.shortcode_path]:
                with open(path) as g:
                    f.writelines(g.readlines())
        argv = ['script_name', combined_path, '-o', self.out_dir + '/Preprocessor/shortcode_resolved.h']
        print('* Resolve macros of shortcode with pcpp...')
        pcpp.pcmd.CmdPreprocessor(argv)

    def load_insn_behavior(self):
        print('* Load instruction/behavior pairs.')
        with open(self.out_dir + '/Preprocessor/shortcode_resolved.h') as f:
            for line in f.readlines():
                if line[0] == '#':
                    continue
                insn_name, insn_beh = self.split_resolved_shortcode(line)
                if '__COMPOUND_PART1__' not in insn_beh:
                    self.behaviors[insn_name] = [insn_beh]
                    continue
                ib1, ib2 = self.split_compounds(insn_beh)
                self.behaviors[insn_name] = [ib1, ib2]

    def get_insn_behavior(self, insn_name) -> [str]:
        """ Returns a list of instruction behaviors. Most instruction will only have one element in the list.
            But there are instructions which have multiple behaviors (Compounds in our case).
        """

        for i in self.behaviors.keys():
            if i == insn_name:
                return self.behaviors[insn_name]
        return None

    @staticmethod
    def split_compounds(insn_beh: str) -> (str, str, str, str):
        """ Compound instructions have two parts. In the shortcode the first part is surrounded
            with "__COMPOUND_PART1__".
            We move this part to its own instruction and return <insn>_part1, <insn>_part2
        """

        match = re.match(r'\{.*__COMPOUND_PART1__(\{.+})__COMPOUND_PART1__(.*)}$', insn_beh)
        beh_p1 = match.group(1)
        beh_p2 = match.group(2)
        return beh_p1, beh_p2

    @staticmethod
    def split_resolved_shortcode(line: str) -> (str, str):
        """ Splits a shortcode line into a tuple of instruction ID and behavior. """

        match = re.search(rf'insn\((\w+), (.+)\)$', line, re.ASCII)
        if not match:
            raise ValueError(f'Could not split shrtcode line: {line}')
        return match.group(1), match.group(2)


if __name__ == '__main__':
    print("Not implemented.")
