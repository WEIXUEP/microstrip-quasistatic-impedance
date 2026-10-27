# Development & publishing

## Repository layout

```text
microstrip_quasistatic.py   Geometry, mesh, FEM, CLI, and JSON output
requirements.txt           Solver dependencies
requirements-docs.txt      Documentation dependencies
README.md                  English repository entry point
mkdocs.yml                 Site configuration and navigation
doc/                       English pages, diagrams, styles, and local fonts
overrides/                 MkDocs theme templates
.github/workflows/docs.yml Documentation checks and Pages deployment
```

`.venv/`, `output/`, and `site/` are local environments or generated files and are excluded from version control.

## Python API {#python-api}

The module can be imported without running `main()`.

| Interface | Inputs | Return / effect |
| --- | --- | --- |
| `MicrostripGeometry(...)` | Lengths in mil, permittivities, domain and mesh factors | Frozen dataclass |
| `generate_mesh(p, mesh_path)` | Geometry and output `Path` | Writes `.msh`; returns `MeshData` |
| `solve_electrostatic(mesh, p, vacuum, order)` | Mesh, matching geometry, vacuum flag, order 1/2 | `(potential, capacitance_per_length)` |

`MeshData.points` has shape `(N, 2)` and coordinates in meters. `triangles` has shape `(M, 3)` with zero-based vertex indices; `relative_permittivity` has length M. `signal_nodes` and `ground_nodes` contain vertex indices. The solver re-identifies fixed-potential DOFs from physical coordinates to include P2 edge midpoints.

`potential` follows the finite-element DOF ordering. With P2, its length generally exceeds the vertex count and does not match the original Gmsh node order. Capacitance is returned in F/m.

### Dataclass defaults

| Field | Default | Unit |
| --- | ---: | --- |
| `h1`, `h2` | 2.97, 3.53 | mil |
| `w1`, `w2` | **5.60, 5.60** | mil |
| `trace_thickness` | 1.80 | mil |
| `er1`, `er2` | 4.20, 4.20 | Dimensionless |
| `substrate_width_factor` | 30.0 | Dimensionless |
| `air_padding_x_factor` | 10.0 | Dimensionless |
| `air_padding_top_factor` | 10.0 | Dimensionless |
| `air_padding_bottom_factor` | 2.0 | Dimensionless |
| `trace_mesh_area_factor` | 50.0 | Dimensionless |
| `far_mesh_area_factor` | 400.0 | Dimensionless |
| `mesh_size_trace` | 0.12 | mil |
| `mesh_size_far` | 3.0 | mil |

The dataclass does not automatically derive target sizes from area factors. `generate_mesh()` directly uses `mesh_size_trace` and `mesh_size_far`. The CLI's `main()` applies the [area formulas](cli.md#mesh-area-factors) through `dataclasses.replace()`. When using the API, explicitly choose manual sizes or area-derived ones.

### Minimal API example

Save this as a separate script in the project root and run it with the virtual environment:

```python
from dataclasses import replace
from math import sqrt
from pathlib import Path
from scipy.constants import c
from microstrip_quasistatic import (
    MicrostripGeometry, generate_mesh, solve_electrostatic,
)

p = MicrostripGeometry(w1=10.0, w2=5.6)
p = replace(
    p,
    mesh_size_trace=sqrt(p.trace_area / p.trace_mesh_area_factor),
    mesh_size_far=sqrt(p.simulation_area / p.far_mesh_area_factor),
)
mesh = generate_mesh(p, Path("output/api/microstrip.msh"))
potential, capacitance = solve_electrostatic(mesh, p, vacuum=False, order=2)
_, vacuum_capacitance = solve_electrostatic(mesh, p, vacuum=True, order=2)
impedance = 1.0 / (c * sqrt(capacitance * vacuum_capacitance))
print(f"Z0 = {impedance:.6f} ohm")
```

`generate_mesh()` initializes and finalizes its own Gmsh session. Do not nest it inside a separately managed Gmsh session.

## Preview the documentation

Install the documentation dependencies from the repository root. No solver dependencies or simulation run are required:

```shell
python -m pip install -r requirements-docs.txt
python -m mkdocs serve
```

Open the URL shown in the terminal, usually [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Changes refresh automatically. On Windows, replace `python` with `.\.venv\Scripts\python.exe` when needed.

Build deployable HTML:

```shell
python -m mkdocs build --strict
```

The output is in `site/`. Preview over HTTP so directory links and search work correctly:

```shell
python -m http.server 8000 --directory site
```

## Interface design

The English interface uses an annotated cross section as the overview's main visual, with blue dielectric regions and copper conductors. Chapter navigation stays on the left; reference pages add an in-page contents list on the right. On smaller screens the introduction stacks above the diagram and navigation moves into a drawer.

`doc/assets/stylesheets/engineering.css` defines colors, spacing, responsive layouts, focus indicators, and light/dark styles. `overrides/main.html` wraps the overview content for customization. Search, navigation, copy buttons, and theme controls use MkDocs Material's English UI.

IBM Plex Sans and IBM Plex Mono are self-hosted under `doc/assets/fonts/`; their SIL Open Font License is included there. Site visitors do not need to load fonts from a third-party font service. The geometry diagram and project mark are editable SVGs.

## Publish to GitHub Pages {#github-pages}

Site URL:

**[https://weixuep.github.io/microstrip-quasistatic-impedance/](https://weixuep.github.io/microstrip-quasistatic-impedance/)**

Initial setup requires repository administration access:

1. Commit the documentation and `.github/workflows/docs.yml` to `main`.
2. Under **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**.
3. Under **Actions → Documentation → Run workflow**, select `main` and run, or push a documentation change.
4. Wait for both build and deploy to succeed, then open the project URL.

No personal access token or additional secret is required by the workflow. Deployment uses `GITHUB_TOKEN` and OIDC; Pages write permissions are limited to the deploy job. If environment rules require review, complete that review on GitHub.

Changes to `doc/`, `overrides/`, `mkdocs.yml`, documentation dependencies, or the workflow trigger publishing when pushed to `main`. Pull requests build and upload a `documentation-html` artifact for review. Manual runs also support republishing; branches other than `main` do not deploy. Releases are serialized to avoid canceling an active deployment.

For a fork or repository move, update `site_url`, `repo_url`, and `repo_name` in `mkdocs.yml`, plus the README and the URL above. If the default branch changes, also update workflow conditions and `edit_uri`.

## Maintenance checks

After editing documentation, run the strict build and fix internal links, navigation, and configuration warnings. Add new pages to `nav` in `mkdocs.yml`. Strict mode does not check remote URLs; verify the published pages and search after deployment.

Keep all documentation, navigation labels, alternative text, and interface controls in English. When changing the design, inspect desktop and mobile layouts, dark mode, tables, keyboard focus, navigation, and search. Font or SVG updates must preserve their licenses and accessible descriptions.

When changing the solver, check default execution, vacuum consistency, and convergence relevant to the change. Update documentation when parameters, defaults, units, output fields, or boundary behavior change. Preserve the provenance of historical comparisons and provide reproducible settings for new accuracy claims.
