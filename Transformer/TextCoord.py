# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

class TextCoord:
    """
    Coordinates into text.
    """
    def __init__(self):
        self.start_pos: int = -1
        self.end_pos: int = -1

    def __getattr__(self, name):
        if name == "len":
            return self.end_pos - self.start_pos
        raise AttributeError(f"Attribute {name} does not exist.")

    def __str__(self):
        return f"s: {self.start_pos} e: {self.end_pos}"
