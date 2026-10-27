# Quasi-Static Microstrip Impedance

A standalone Python demo for computing the quasi-TEM characteristic impedance
of a two-layer microstrip cross section with a finite-width ground plane.
Gmsh builds the geometry and mesh; scikit-fem and SciPy solve the electrostatic
finite element problems. No Palace or other external EM solver is required.

**[Read the documentation](https://weixuep.github.io/microstrip-quasistatic-impedance/)**
| [Documentation sources](doc/index.md)

![Microstrip cross section](doc/microstrip_geometry.svg)

## Quick start

Requires Python **3.10+**. All geometry inputs are in **mil** (`1 mil = 25.4 μm`).

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe microstrip_quasistatic.py
```

Linux / macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python microstrip_quasistatic.py
```

Custom case (use your virtual environment's Python):

```shell
python microstrip_quasistatic.py --h1 5 --h2 5 --er1 3.66 --er2 4.2 --w1 20 --w2 50 --trace-thickness 1 --order 2 --output output/custom
```

W1 is the bottom trace width, W2 the top width, and T the trace thickness.
The trace starts at the dielectric interface and extends into the upper layer;
H2 includes T, so `0 < T < H2`. Use equal W1/W2 for a rectangular trace.
See the [complete CLI reference](doc/cli.md) for defaults and mesh controls.

## Results and model

The script solves the real dielectric case for capacitance C and an otherwise
identical vacuum case for C0, then computes:

```text
epsilon_eff = C / C0
Z0 = 1 / (c * sqrt(C * C0))
L = 1 / (c² * C0)
vp = c / sqrt(epsilon_eff)
```

Default outputs are `output/microstrip.msh` and `output/result.json` beside the
script. Capacitances are in F/m and impedance is in ohms. Exported mesh
coordinates remain in mil; only the in-memory FEM coordinates are in meters.
The mesh includes metal triangles that are excluded from the FEM solve and
contains no physical groups or field results. See the [output reference](doc/output.md).

The outer air-box boundary uses a zero-normal-flux natural condition. This is
a finite-domain, lossless quasi-static model without frequency-dependent or
full-wave effects. Check [mesh and domain convergence](doc/validation.md) before
using a result as an engineering reference.

The [five historical Polar SI9000 comparisons](doc/validation.md#polar-si9000)
are preserved, with a largest reported relative difference of about 0.72%.
Their original mesh and Polar setup were not fully recorded; they are not a
general accuracy guarantee.

## Build the documentation website

The English documentation uses a custom engineering interface with an annotated
cross section, chapter navigation, search, and light/dark themes. Fonts are
self-hosted. Documentation dependencies are separate from solver dependencies.

```shell
python -m pip install -r requirements-docs.txt
python -m mkdocs serve
```

Open the localhost URL shown in the terminal. Build static HTML with:

```shell
python -m mkdocs build --strict
```

The generated website is in `site/`. The [Documentation workflow](.github/workflows/docs.yml)
builds pull requests and publishes main-branch changes to GitHub Pages.
For initial Pages configuration and maintenance, see the
[deployment guide](doc/development.md#github-pages).

## License

[Apache License 2.0](LICENSE).
