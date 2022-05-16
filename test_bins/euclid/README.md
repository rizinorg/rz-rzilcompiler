## Extended Euclid Algorithm

The test binary calculates the greatest common divisor with the help of Extended Euclids algorithm.

The build script builds object files with an optimization of 0-3
and two linked binaries with optimization 0 and 3.

Each binary should contain unique instructions and is therefore different to emulate, while the result should stay the same.

The `gen_stats.sh` script runs Rizins `aaa` command on each of those binaries and writes the disassembled instructions into stat files.
Rizin needs to be patched in a way that it prints the disassembled instructions to `stdout`.

For comparison there is also a x86 binary which prints the results of `gcd(63,22)` (which is the hard coded calculation performed in the binaries).
