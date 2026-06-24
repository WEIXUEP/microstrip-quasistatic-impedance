# Pure Python Quasi-Static Microstrip Impedance Demo

This is a small standalone demo for computing the characteristic impedance of
a 2D microstrip cross section using a quasi-static finite element method.

It does not call Palace or any other external EM solver. Geometry and meshing
are handled by the Gmsh Python API; the electrostatic finite element solve is
assembled with `scikit-fem` and solved with SciPy.

## What It Does

The script solves two electrostatic problems on the same 2D cross section:

1. The real dielectric case, which gives the per-unit-length capacitance `C`.
2. The vacuum reference case, which gives the free-space capacitance `C0`.

The quasi-TEM impedance is then computed from:

```text
epsilon_eff = C / C0
Z0 = 1 / (c0 * sqrt(C * C0))
```

All geometry inputs are in `mil`. The finite element solve is performed in SI
units, so capacitance is reported directly in `F/m`.

## Geometry
![Microstrip geometry](doc/microstrip_geometry.svg)

The demo models a microstrip-like cross section with:

- two dielectric layers,
- a finite ground plane at the bottom of the lower dielectric,
- a rectangular or trapezoidal signal trace at the interface between the two
  dielectric layers,
- an enclosing air box.

The trace shape is controlled by:

```text
W1 = lower trace width
W2 = upper trace width
T  = trace thickness
```

If `W1 == W2`, the trace is rectangular. If `W1 != W2`, the trace is
trapezoidal.

## Install

Using a virtual environment is recommended:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

Run the default case:

```bash
.venv/bin/python microstrip_quasistatic.py
```

Run a custom case:

```bash
.venv/bin/python microstrip_quasistatic.py \
  --h1 5 \
  --h2 5 \
  --er1 3.66 \
  --er2 4.2 \
  --w1 20 \
  --w2 50 \
  --trace-thickness 1 \
  --order 2
```

Generated files are written to `output/` by default:

```text
output/microstrip.msh
output/result.json
```

## Main Options

| Option | Meaning |
|---|---|
| `--h1` | Lower dielectric height in mil |
| `--h2` | Upper dielectric height in mil |
| `--er1` | Lower dielectric relative permittivity |
| `--er2` | Upper dielectric relative permittivity |
| `--w1` | Lower trace width in mil |
| `--w2` | Upper trace width in mil |
| `--trace-thickness` | Trace thickness in mil |
| `--order` | FEM order, `1` or `2` |
| `--trace-mesh-area-factor` | Controls near-trace mesh size |
| `--far-mesh-area-factor` | Controls far-field mesh size |
| `--output` | Output directory |

Near-trace and far-field mesh sizes are derived automatically from area-based
factors:

```text
mesh_size_trace = sqrt(trace_area / trace_mesh_area_factor)
mesh_size_far = sqrt(simulation_area / far_mesh_area_factor)
```

## Output

`result.json` contains:

- input geometry,
- mesh size and finite element order,
- capacitance `C`,
- vacuum capacitance `C0`,
- effective permittivity,
- equivalent inductance,
- phase velocity,
- characteristic impedance `Z0`.

## Comparison With Polar SI9000

The following cases compare this Python quasi-static FEM implementation against
Polar SI9000. All dimensions are in `mil`, and all impedances are in `Ohm`.

| Case | H1 | Er1 | H2 | Er2 | W1 | W2 | T | Python FEM Z0 | Polar SI9000 Z0 | Difference | Relative Difference |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10.0000 | 4.2000 | 3.5300 | 4.2000 | 10.0000 | 5.6000 | 1.8000 | 64.140182488122 | 63.98 | +0.160182488122 | 0.2504% |
| 2 | 10.0000 | 9.6000 | 20.0000 | 2.2000 | 20.0000 | 10.0000 | 5.0000 | 31.435874124034 | 31.49 | -0.054125875966 | 0.1719% |
| 3 | 20.0000 | 3.6600 | 20.0000 | 2.2000 | 50.0000 | 30.0000 | 4.0000 | 43.290042581624 | 43.28 | +0.010042581624 | 0.0232% |
| 4 | 5.0000 | 3.6600 | 5.0000 | 4.2000 | 20.0000 | 50.0000 | 1.0000 | 16.375774087632 | 16.26 | +0.115774087632 | 0.7120% |
| 5 | 5.0000 | 3.6600 | 5.0000 | 4.2000 | 1.0000 | 1.0000 | 1.0000 | 91.810012129350 | 91.73 | +0.080012129350 | 0.0872% |

The largest relative difference in these cases is about `0.72%`.
