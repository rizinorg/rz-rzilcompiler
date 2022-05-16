#!/bin/sh

gcc -o euclid_x86 euclid.c

hexagon-clang -c -O3 -DHEXAGON_BUILD=1 -o hexagon/hex_O3.o euclid.c
hexagon-clang -c -O2 -DHEXAGON_BUILD=1 -o hexagon/hex_O2.o euclid.c
hexagon-clang -c -O1 -DHEXAGON_BUILD=1 -o hexagon/hex_O1.o euclid.c
hexagon-clang -c -O0 -DHEXAGON_BUILD=1 -o hexagon/hex_O0.o euclid.c

hexagon-clang -O3 -DHEXAGON_BUILD=1 -o hexagon/hex_O3.bin euclid.c
hexagon-clang -O0 -DHEXAGON_BUILD=1 -o hexagon/hex_O0.bin euclid.c
