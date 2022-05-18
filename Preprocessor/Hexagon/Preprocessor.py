#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

import sys


class Preprocessor:

    def __init__(self, shortcode_path: str, macros_paths: list, out_path: str):
        pass

    def preprocess_macros(self, out_path: str):
        """ Remove includes. Decide between QEMU_GENERATE or not. """
        pass

    def preprocess_shortcode(self, out_path: str):
        """ Run pcpp on shortcode + macro files. """
        pass


if __name__ == '__main__':
    print("Not implemented.")
