#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from rzilcompiler.Tests.TestHybrids import TestHybrids
from rzilcompiler.Tests.TestTransformer import (
    TestTransforming,
    TestTransformerMeta,
    TestGrammar,
    TestTransformerOutput,
    TestTransformedInstr,
)
from rzilcompiler.Tests.TestHelper import TestHelper
from rzilcompiler.Tests.TestParser import TestParser

if __name__ == "__main__":
    TestHybrids().main()
    TestTransforming().main()
    TestTransformerMeta().main()
    TestGrammar().main()
    TestTransformerOutput().main()
    TestTransformedInstr().main()
    TestHelper().main()
    TestParser().main()
