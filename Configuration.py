# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import subprocess

from enum import StrEnum
from pathlib import Path


class InputFile(StrEnum):
    """
    Enum of paths used by the components.

    <REPO> is replaced with the path to the repositories root.
    <ARCH> is replaced with the architecture name.
    """

    GRAMMAR = "<REPO>/Resources/<ARCH>/grammar.lark"
    HEXAGON_PP_COMBINED_H = "<REPO>/Resources/Hexagon/Preprocessor/combined.h"
    HEXAGON_PP_MACROS_H = "<REPO>/Resources/Hexagon/Preprocessor/macros.h"
    HEXAGON_PP_MACROS_MMVEC_H = "<REPO>/Resources/Hexagon/Preprocessor/macros_mmvec.h"
    HEXAGON_PP_MACROS_PATCHES_H = (
        "<REPO>/Resources/Hexagon/Preprocessor/macros_patches.h"
    )
    HEXAGON_PP_SHORTCODE_H = "<REPO>/Resources/Hexagon/Preprocessor/shortcode.h"
    HEXAGON_PP_SHORTCODE_RESOLVED_H = (
        "<REPO>/Resources/Hexagon/Preprocessor/shortcode_resolved.h"
    )
    HEXAGON_PP_SHORTCODE_RESOLVED_TMP_H = (
        "<REPO>/Resources/Hexagon/Preprocessor/shortcode_resolved_tmp.h"
    )
    HEXAGON_PP_PATCHED_MACROS_H = (
        "<REPO>/Resources/Hexagon/Preprocessor/patched_macros.h"
    )


class Conf:
    """
    Holds all the configurable values like paths.
    """

    @staticmethod
    def replace_placeholders(path_str: str, arch: str = "") -> str:
        if "<REPO>" in path_str:
            root = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                stdout=subprocess.PIPE,
            )
            path_str = path_str.replace(
                "<REPO>", root.stdout.decode("utf8").strip("\n")
            )
        if "<ARCH>" in path_str:
            if not arch:
                raise ValueError("No architecture name passed.")
            path_str = path_str.replace("<ARCH>", arch)
        return path_str

    @staticmethod
    def get_path(file: InputFile, arch_name: str = "") -> Path:
        return Path(Conf.replace_placeholders(str(file), arch_name))
