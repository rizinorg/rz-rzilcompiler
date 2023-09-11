# SPDX-FileCopyrightText: 2023 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

ExpectedOutput = {
    "Y2_barrier": ("\n"
                   "// READ\n"
                   "\n"
                   "// EXEC\n"
                   "\n"
                   "// WRITE\n"
                   "RzILOpEffect *empty_seq_0 = EMPTY();\n"
                   "RzILOpEffect *instruction_sequence = SEQN(1, empty_seq_0);\n"
                   "\n"
                   "return instruction_sequence;"
                   )
}
