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
python -m unittest Tests/TestTransformer.py
```


