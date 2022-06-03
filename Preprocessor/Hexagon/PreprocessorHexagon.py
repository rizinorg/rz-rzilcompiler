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
            for l in f.readlines():
                if l[0] == '#':
                    continue
                match = re.search(r'insn\((\w+), (.+)\)$', l, re.ASCII)
                self.behaviors[match.group(1)] = match.group(2)

    def get_insn_behavior(self, insn_name):
        for i in self.behaviors.keys():
            if i == insn_name:
                return self.behaviors[insn_name]
        return None


if __name__ == '__main__':
    print("Not implemented.")
