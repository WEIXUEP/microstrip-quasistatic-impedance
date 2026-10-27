# Installation & first run

Run a default cross section, then change the geometry and read its impedance.

## Requirements

- Python **3.10 or newer**. The documentation workflow uses Python 3.11.
- Network access to install Python packages.
- Native libraries required by the Gmsh Python wheel. A separate Gmsh desktop installation is not required.

The solver dependencies in `requirements.txt` are Gmsh, NumPy, SciPy, and scikit-fem. Documentation dependencies are separate; you do not need them to run a calculation.

## Clone the repository

```shell
git clone https://github.com/WEIXUEP/microstrip-quasistatic-impedance.git
cd microstrip-quasistatic-impedance
```

## Windows PowerShell

Call the virtual environment's Python directly. This avoids activating a script or changing your execution policy.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe microstrip_quasistatic.py
```

Inspect the command-line help:

```powershell
.\.venv\Scripts\python.exe microstrip_quasistatic.py --help
```

## Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python microstrip_quasistatic.py
```

Minimal Ubuntu/Debian installations may need `python3-venv` and `libglu1-mesa`. See [troubleshooting](troubleshooting.md) for native-library errors.

## Run a custom trace {#custom-case}

This example uses H1=5, H2=5, W1=20, W2=50, and T=1 mil, with second-order finite elements. The single-line command works in PowerShell and Bash. Replace `python` with the appropriate virtual-environment path above, or activate the environment first.

```shell
python microstrip_quasistatic.py --h1 5 --h2 5 --er1 3.66 --er2 4.2 --w1 20 --w2 50 --trace-thickness 1 --order 2 --output output/custom
```

W2 > W1 makes this a trace with a wider top than bottom. To model a rectangular trace, explicitly set `--w1` and `--w2` to the same value. H2 includes the trace thickness, so `0 < T < H2`.

## Inspect the result

The terminal prints mesh vertices, triangles, finite-element degrees of freedom, capacitances, phase velocity, inductance, and impedance. The default files are:

```text
output/
├── microstrip.msh
└── result.json
```

Read the main fields with Python:

```python
import json
from pathlib import Path

result = json.loads(Path("output/result.json").read_text(encoding="utf-8"))
print(f"Z0 = {result['characteristic_impedance_ohm']:.6f} ohm")
print(f"Effective permittivity = {result['effective_permittivity']:.6f}")
```

An explicit relative `--output` path is relative to the current working directory. Without this option, files go to `output/` beside the script. Reusing a directory overwrites the previous files; choose separate directories for parameter sweeps.

Continue with the [geometry definition](geometry.md), [complete CLI reference](cli.md), or [convergence checks](validation.md).
