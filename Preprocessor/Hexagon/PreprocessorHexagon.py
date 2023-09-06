#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import re
import pcpp

from pathlib import Path

from Configuration import InputFile, Conf


class PreprocessorHexagon:
    behaviors = dict()
    patched_macros = []

    def __init__(self, shortcode_path: Path):
        self.shortcode_path: Path = shortcode_path

    def run_preprocess_steps(self):
        self.preprocess_macros()
        self.preprocess_shortcode()
        self.postprocess_shortcode()

    def preprocess_macros(self):
        """Remove includes. Decide between QEMU_GENERATE or not. Patch certain macros with ou version."""
        m = self.cleanup_macros()
        with open(Conf.get_path(InputFile.HEXAGON_PP_MACROS_PATCHED_H), "w") as f:
            f.writelines("\n".join(self.patch_macros(m)))

    def cleanup_macros(self) -> [str]:
        """Removes all guards, includes and comments from the macro files."""
        res = []
        for mp in [
            Conf.get_path(InputFile.HEXAGON_PP_MACROS_H),
            Conf.get_path(InputFile.HEXAGON_PP_MACROS_MMVEC_H),
        ]:
            if "mmvec" in mp.name:
                is_vec_macro_file = True
            else:
                is_vec_macro_file = False
            with open(mp) as f:
                in_qemu_gen = False
                in_user_only = False
                for line in f.readlines():
                    if line == "\n":
                        continue
                    if re.match(r"#ifdef QEMU_GENERATE", line):
                        in_qemu_gen = True
                        continue
                    if re.match(r"#ifdef CONFIG_USER_ONLY", line):
                        in_user_only = True
                        continue
                    if re.match(r"#ifndef|#ifdef", line):
                        continue
                    if re.match(r"#include", line):
                        continue
                    if re.match(r"(#else)|(#endif)", line):
                        if in_qemu_gen or in_user_only:
                            in_user_only = False
                            in_qemu_gen = False
                        continue
                    if in_qemu_gen and is_vec_macro_file:
                        # QEMU_GENERATE macros of the vector macro file are included.
                        res.append(line.strip("\n"))
                        continue
                    elif in_qemu_gen or in_user_only:
                        continue
                    if re.match(r"(\s*//)|(/\*)|(\s*\*)", line):  # Ignore comments
                        continue
                    res.append(line.strip("\n"))
        # Join lines with an \ at the end
        i = 0
        while i != len(res):
            if not re.search(r"\\\s*$", res[i]):
                # One line macro
                i += 1
                continue
            try:
                res[i] = re.sub(r"\\\s*$", " ", res[i]).strip() + res.pop(i + 1)
            except IndexError:
                raise IndexError(f'Last line in macro file ends with a "\\": {res[i]}.')

        return res

    def patch_macros(self, macros: [str]):
        # Read macro patches
        with open(Conf.get_path(InputFile.HEXAGON_PP_PATCHES_MACROS_H)) as f:
            cont = "".join(f.readlines())
            cont = re.sub(r"\\\s*\n", "", cont)

        # Get macro names and store their lines.
        patches = dict()
        for line in cont.split("\n"):
            if not re.search(r"^#define", line):
                continue
            match = re.search(r"^#define\s+([\w_]*).*", line)
            if not match:
                raise ValueError(f'Macro patch "{line}" not properly formatted.')
            patches[match.group(1)] = line

        # Patch
        patched = []
        for macro in macros:
            m_name = re.search(r"^#define\s+([\w_]*).*", macro).group(1)
            if m_name in patches.keys():
                patched.append(patches.pop(m_name))
            else:
                patched.append(macro)
        # Prepend macros which don't replace any (user defined once)
        for m in patches.values():
            patched.insert(0, m)
        return patched

    def preprocess_shortcode(self):
        """Run pcpp on shortcode + macro files."""
        combined_path = Conf.get_path(InputFile.HEXAGON_PP_COMBINED_H)
        with open(combined_path, "w") as f:
            with open(Conf.get_path(InputFile.HEXAGON_PP_MACROS_PATCHED_H)) as g:
                f.writelines(g.readlines())
            f.write("\n")
            with open(self.shortcode_path) as g:
                f.writelines(g.readlines())
        argv = [
            "script_name",
            str(combined_path),
            "-o",
            str(Conf.get_path(InputFile.HEXAGON_PP_SHORTCODE_RESOLVED_TMP_H)),
        ]
        print("* Resolve macros of shortcode with pcpp...")
        pcpp.pcmd.CmdPreprocessor(argv)
        print("* Do it again due to https://github.com/ned14/pcpp/issues/71")
        argv = [
            "script_name",
            str(Conf.get_path(InputFile.HEXAGON_PP_MACROS_PATCHED_H)),
            str(Conf.get_path(InputFile.HEXAGON_PP_SHORTCODE_RESOLVED_TMP_H)),
            "-o",
            str(Conf.get_path(InputFile.HEXAGON_PP_SHORTCODE_RESOLVED_H)),
        ]
        pcpp.pcmd.CmdPreprocessor(argv)

    def load_insn_behavior(self):
        print("* Load instruction/behavior pairs.")
        with open(Conf.get_path(InputFile.HEXAGON_PP_SHORTCODE_RESOLVED_H)) as f:
            for line in f.readlines():
                if line[0] == "#":
                    continue
                insn_name, insn_beh = self.split_resolved_shortcode(line)
                if "__COMPOUND_PART1__" not in insn_beh:
                    self.behaviors[insn_name] = [insn_beh]
                    continue
                ib1, ib2 = self.split_compounds(insn_beh)
                self.behaviors[insn_name] = [ib1, ib2]

    def get_insn_behavior(self, insn_name) -> [str]:
        """Returns a list of instruction behaviors. Most instruction will only have one element in the list.
        But there are instructions which have multiple behaviors (Compounds in our case).
        """

        for i in self.behaviors.keys():
            if i == insn_name:
                return self.behaviors[insn_name]
        return None

    @staticmethod
    def split_compounds(insn_beh: str) -> (str, str, str, str):
        """Compound instructions have two parts. In the shortcode the first part is surrounded
        with "__COMPOUND_PART1__".
        We move this part to its own instruction and return <insn>_part1, <insn>_part2
        """

        match = re.match(
            r"\{.*__COMPOUND_PART1__(\{.+})__COMPOUND_PART1__(.*)}$", insn_beh
        )
        beh_p1 = match.group(1)
        beh_p2 = "{" + match.group(2) + "}"  # brackets were excluded in regex.
        return beh_p1, beh_p2

    @staticmethod
    def split_resolved_shortcode(line: str) -> (str, str):
        """Splits a shortcode line into a tuple of instruction ID and behavior."""

        match = re.search(rf"insn\((\w+), (.+)\)$", line, re.ASCII)
        if not match:
            raise ValueError(f"Could not split shrtcode line: {line}")
        return match.group(1), match.group(2)

    @staticmethod
    def replace_do_while_0(code: str) -> str:
        m = re.search(r"(.*)do\s*\{(.*)}\s*while\s*\(0\)(.*)", code)
        if not m:
            return code
        tmp = ""
        while m:
            tmp = m.group(1) + m.group(2) + m.group(3)
            m = re.search(r"(.*)do\s*\{(.*)}\s*while\s*\(0\)(.*)", tmp)
        return tmp + "\n"

    def postprocess_shortcode(self):
        self.remove_onetime_do_whiles()

    def remove_onetime_do_whiles(self):
        """Removes the `do {...} while(0)` pattern from the shortcode."""
        path = Conf.get_path(InputFile.HEXAGON_PP_SHORTCODE_RESOLVED_H)
        res = []
        with open(path) as f:
            for line in f.readlines():
                res.append(self.replace_do_while_0(line))
        with open(path, "w") as f:
            f.writelines(res)


if __name__ == "__main__":
    print("Not implemented.")
