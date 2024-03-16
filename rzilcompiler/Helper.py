# SPDX-FileCopyrightText: 2022 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: LGPL-3.0-only

from enum import IntEnum

try:
    from colorama import init, Fore, Style

    init()
    colorama_imported = True
except ImportError:
    print("colorama package not found. Enjoy your Script Noire :)")
    colorama_imported = False


class LogLevel(IntEnum):
    TODO = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    VERBOSE = 5


LOG_LEVEL = LogLevel.INFO


def log(msg: str, verbosity: LogLevel = LogLevel.INFO) -> None:
    """

    Args:
        msg: The message to log
        verbosity: msg level: error, log

    Returns: None

    """
    if verbosity > LOG_LEVEL:
        return

    if colorama_imported:
        if verbosity == LogLevel.ERROR:
            print(
                "["
                + Fore.RED
                + "X"
                + Style.RESET_ALL
                + "] {}".format(Fore.RED + msg + Style.RESET_ALL)
            )
        elif verbosity == LogLevel.WARNING:
            print(
                "["
                + Fore.LIGHTYELLOW_EX
                + "!"
                + Style.RESET_ALL
                + "] {}".format(Fore.LIGHTYELLOW_EX + msg + Style.RESET_ALL)
            )
        elif verbosity == LogLevel.INFO:
            print("[" + Fore.BLUE + "*" + Style.RESET_ALL + "] {}".format(msg))
        elif verbosity == LogLevel.DEBUG:
            print(
                "[" + Fore.LIGHTMAGENTA_EX + "#" + Style.RESET_ALL + "] {}".format(msg)
            )
        elif verbosity == LogLevel.VERBOSE:
            print("[" + Fore.LIGHTWHITE_EX + "-" + Style.RESET_ALL + "] {}".format(msg))
        elif verbosity == LogLevel.TODO:
            print("[" + Fore.GREEN + "T" + Style.RESET_ALL + "] {}".format(msg))

    else:
        if verbosity == LogLevel.ERROR:
            print("[X] {}".format(msg))
        elif verbosity == LogLevel.WARNING:
            print("[!] {}".format(msg))
        elif verbosity == LogLevel.INFO:
            print("[*] {}".format(msg))
        elif verbosity == LogLevel.DEBUG:
            print("[#] {}".format(msg))
        elif verbosity == LogLevel.VERBOSE:
            print("[-] {}".format(msg))
        elif verbosity == LogLevel.TODO:
            print("[T] {}".format(msg))
