<!--
SPDX-FileCopyrightText: 2023 Rot127

SPDX-License-Identifier: LGPL-3.0-only
-->

# rzil-hexagon

C to RzIL Compiler to extend the Rizin Hexagon plugin.

## Install

```bash
# Python 3.11 required
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
pip3 install -e .
```

## Run

**Compile all instructions and show exceptions which occurred.**

```bash
./Compiler.py -a Hexagon -t
```

**Run tests**

```bash
python -m unittest Tests/test_all.py
```

## Code generation

### Typing

During transformation every value gets a type assigned (see: `ValueType.py`).

For readability `ValueTypes` are printed in the form `st32`, `ut8` etc.

Because QEMU uses C types in their definitions, we translate these types specifiers to
`ValueTypes` as well.

So `uint32_t` is an unsigned bitvector of 32bits. `ValueTypes` should not be interpreted
as integers! By default they only describe the bitvector.

Further interpretation of the bitvector can be specified in `ValueType.group` (e.g. `FLOAT`, `VOID` etc.)

**External Types**

Some parameters are not meant to be used by the VM.
For example, if you have a sub-routine which reads a register value,
you might need to pass the register name as string to it. 

Those kinds of parameters must be represented in the type checking system as well.
Although, they are never seen by the VM.
For this they have the `VTGroup.EXTERNAL` flag set.

Those external types are mostly ignored by the compiler.
It only makes sure that they are not used at incorrect places.
