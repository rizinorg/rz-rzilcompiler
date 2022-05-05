# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

class OverloadException(BaseException):
    def __init__(self, message):
        message = "\nPlease overload this method.\n" + message
        super().__init__(message)
