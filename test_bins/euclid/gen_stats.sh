#!/bin/sh

echo "Assumes rizin prints the instrucions IDs to stdout."

rizin -qq -A hexagon/hex_O3.o 2> /dev/null | sort | uniq -c | sort -g -r > stats/obj_O0.stats
rizin -qq -A hexagon/hex_O2.o 2> /dev/null | sort | uniq -c | sort -g -r > stats/obj_O1.stats
rizin -qq -A hexagon/hex_O1.o 2> /dev/null | sort | uniq -c | sort -g -r > stats/obj_O2.stats
rizin -qq -A hexagon/hex_O0.o 2> /dev/null | sort | uniq -c | sort -g -r > stats/obj_O3.stats

rizin -qq -A hexagon/hex_O3.bin 2> /dev/null | sort | uniq -c | sort -g -r > stats/bin_O3.stats
rizin -qq -A hexagon/hex_O0.bin 2> /dev/null | sort | uniq -c | sort -g -r > stats/bin_O0.stats
