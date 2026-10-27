# Convergence & benchmarks

Use consistency checks first, refinement second, and external comparisons after the model definitions agree.

## Suggested verification sequence

1. Check dimensions, units, materials, and boundaries.
2. Set both layers to vacuum to check the two-solve workflow and units.
3. Hold geometry fixed while refining the mesh and comparing P1/P2.
4. Enlarge the air box; separately assess finite substrate and ground width.
5. Compare with analytical approximations or another solver using the same cross section.

## Vacuum consistency

```shell
python microstrip_quasistatic.py --er1 1 --er2 1 --output output/vacuum
```

The two electrostatic problems are then identical. Expect `C ≈ C0`, `εeff ≈ 1`, and `vp ≈ c`. This checks consistency, not absolute accuracy: both problems can share the same modeling or discretization error.

## Recorded reference runs

These measurements used solver commit `16f7366`, Python 3.11.17, Gmsh 4.15.2, NumPy 2.4.6, SciPy 1.17.1, and scikit-fem 12.0.2. All used P2 and default area factors 50/400. Dependency changes may affect final digits.

| Input case | FEM vertices | FEM triangles | DOFs | Z0 / Ω | εeff |
| --- | ---: | ---: | ---: | ---: | ---: |
| CLI defaults | 10366 | 20471 | 41203 | 31.55849811 | 3.81678467 |
| Default geometry, Er1=Er2=1 | 10366 | 20471 | 41203 | 61.65455342 | 1.00000000 |
| [Custom quickstart case](quickstart.md#custom-case) | 23377 | 46154 | 92908 | 16.37577408 | 3.46987271 |

For the default case, C was `2.064960745030e-10 F/m` and C0 was `5.410210223165e-11 F/m`. These values help check installation and inputs; assess convergence for your intended use.

## Mesh convergence

Run this script from the repository root. It uses the current Python interpreter, fixes the geometry explicitly, and prints impedance changes across three refinement levels:

```python
import json
import subprocess
import sys
from pathlib import Path

previous = None
for factor in (50, 100, 200):
    output = Path("output") / f"convergence-{factor}"
    subprocess.run([
        sys.executable, "microstrip_quasistatic.py",
        "--h1", "2.97", "--h2", "3.53",
        "--er1", "4.2", "--er2", "4.2",
        "--w1", "10", "--w2", "5.6", "--trace-thickness", "1.8",
        "--order", "2",
        "--trace-mesh-area-factor", str(factor),
        "--far-mesh-area-factor", str(8 * factor),
        "--output", str(output),
    ], check=True)
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    z = result["characteristic_impedance_ohm"]
    change = None if previous is None else 100 * abs(z - previous) / abs(z)
    print(f"factor={factor}, Z0={z:.8f} ohm, change_percent={change}")
    previous = z
```

Inspect C, C0, εeff, and the DOF count as well as Z0. Looking only at impedance can hide cancellation of errors in the two capacitances. You can also hold the area factors fixed and compare `--order 1` with `--order 2`.

Choose a threshold appropriate to your application. For example, less than 0.1% change between successive meshes can be a project-specific criterion; it does not prove absolute error below 0.1%. Larger factors increase memory and runtime. Refine near and far factors separately if you need to isolate the dominant source of error.

## Domain convergence {#domain-convergence}

The CLI does not expose substrate or air-box factors; use the Python API. This example enlarges only the air box, while retaining the substrate, ground, and target mesh sizes:

```python
from dataclasses import replace
from pathlib import Path
from math import sqrt
from scipy.constants import c
from microstrip_quasistatic import (
    MicrostripGeometry, generate_mesh, solve_electrostatic,
)

base = MicrostripGeometry(w1=10.0, w2=5.6)
base = replace(
    base,
    mesh_size_trace=sqrt(base.trace_area / base.trace_mesh_area_factor),
    mesh_size_far=sqrt(base.simulation_area / base.far_mesh_area_factor),
)
for scale in (1.0, 1.5, 2.0):
    p = replace(
        base,
        air_padding_x_factor=base.air_padding_x_factor * scale,
        air_padding_top_factor=base.air_padding_top_factor * scale,
        air_padding_bottom_factor=base.air_padding_bottom_factor * scale,
    )
    mesh = generate_mesh(p, Path(f"output/domain-{scale}/microstrip.msh"))
    _, capacitance = solve_electrostatic(mesh, p, vacuum=False, order=2)
    _, vacuum_capacitance = solve_electrostatic(mesh, p, vacuum=True, order=2)
    impedance = 1.0 / (c * sqrt(capacitance * vacuum_capacitance))
    print(scale, impedance)
```

The target sizes are deliberately taken from `base`, avoiding a coarser far mesh as the box area grows. Changing `substrate_width_factor` also changes substrate width, ground width, and air-box width. That is a separate finite-structure study and needs separate interpretation.

## Historical Polar SI9000 comparison {#polar-si9000}

The table preserves data from the original README. Dimensions are in mil; impedances are in Ω. Difference means `Python − Polar`; relative difference is `abs(Python − Polar) / Polar × 100%`.

| Case | H1 | Er1 | H2 | Er2 | W1 | W2 | T | Python FEM Z0 | Polar SI9000 Z0 | Difference | Relative difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 10.0000 | 4.2000 | 3.5300 | 4.2000 | 10.0000 | 5.6000 | 1.8000 | 64.140182488122 | 63.98 | +0.160182488122 | 0.2504% |
| 2 | 10.0000 | 9.6000 | 20.0000 | 2.2000 | 20.0000 | 10.0000 | 5.0000 | 31.435874124034 | 31.49 | −0.054125875966 | 0.1719% |
| 3 | 20.0000 | 3.6600 | 20.0000 | 2.2000 | 50.0000 | 30.0000 | 4.0000 | 43.290042581624 | 43.28 | +0.010042581624 | 0.0232% |
| 4 | 5.0000 | 3.6600 | 5.0000 | 4.2000 | 20.0000 | 50.0000 | 1.0000 | 16.375774087632 | 16.26 | +0.115774087632 | 0.7120% |
| 5 | 5.0000 | 3.6600 | 5.0000 | 4.2000 | 1.0000 | 1.0000 | 1.0000 | 91.810012129350 | 91.73 | +0.080012129350 | 0.0872% |

The largest reported relative difference across these five cases is approximately **0.72%**. The original records do not include complete dependency versions, convergence studies, or Polar model settings. These are historical comparisons, not exact regression targets across versions or a general accuracy guarantee.

Recompute case 1:

```shell
python microstrip_quasistatic.py --h1 10 --h2 3.53 --er1 4.2 --er2 4.2 --w1 10 --w2 5.6 --trace-thickness 1.8 --order 2 --output output/polar-case-1
```

## Keep reproducible records

For each run, retain the command, `result.json`, `.msh`, Git commit, Python version, and installed dependencies:

```shell
git rev-parse HEAD
python --version
python -m pip freeze > output/environment.txt
```

For an external solver, also record cross-section type, finite or infinite substrate/ground assumptions, boundary distances, conductor thickness and trapezoid direction, material definitions, and convergence settings.
