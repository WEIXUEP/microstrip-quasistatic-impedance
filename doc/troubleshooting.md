# Troubleshooting

## Missing gmsh, skfem, or scipy

The interpreter running the script may differ from the one that installed the packages. Use the same interpreter for both:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe microstrip_quasistatic.py
```

On Linux/macOS, use `.venv/bin/python`. The package is named `scikit-fem`, but its import name is `skfem`.

## Missing libGLU.so.1 on Linux

The Gmsh Python package can load native GUI libraries even when the script does not open a GUI. On Ubuntu/Debian, the usual package is:

```bash
sudo apt-get update
sudo apt-get install libglu1-mesa
```

For other distributions, use the package matching the actual library error. If virtual-environment creation fails, Ubuntu/Debian may also need `python3-venv`.

## DLL load failed on Windows

Confirm that Python and the installed wheel have matching architectures. Try `python -m pip install --upgrade gmsh` for a wheel compatible with the environment. If the problem persists, record the full error, Python version, and architecture, then check the native runtimes required by that wheel.

## Trace thickness must be smaller than h2

The trace extends upward from the layer interface. H2 includes T, so T must be smaller than H2. See the other [input constraints](geometry.md#valid-inputs).

## Failed to identify signal or ground boundaries / DOFs

Check that lengths are positive, the trace fits within the substrate, T < H2, and millimeters were not passed as mil. Extremely small features may approach the absolute tolerances used for boundary identification. That requires reviewing the tolerances in the source; refining the mesh alone may not resolve it.

## Disagreement with Polar or another solver

First align W1/W2 orientation, whether H2 includes copper thickness, material values, finite-ground assumptions, and outer boundaries. Then check mesh and domain convergence separately. The historical benchmark table applies only to its listed cases; see [benchmark limitations](validation.md#polar-si9000).

## The mesh stays first order with --order 2

This is expected. scikit-fem constructs the P2 potential space internally. The Gmsh export remains first order; see [FEM versus mesh order](cli.md#fem-order-versus-mesh-order).

## Too many elements, high memory use, or a slow solve

Larger area factors make the mesh finer. Confirm the geometry with default or coarser settings, then refine gradually. P2 generally uses more degrees of freedom than P1. Avoid enlarging the air box and all mesh factors aggressively at once.

## No field plots, S parameters, or frequency option

The script currently exports a mesh and quasi-static scalar results. Potential values are returned by the solver but are not exported as a field file. S parameters, losses, and full-wave analysis are outside the current implementation.

## Documentation build fails

From the repository root, install `requirements-docs.txt` and run `python -m mkdocs build --strict`. Internal-link or configuration warnings also fail this strict build; correct the items shown in the log.

## GitHub Pages returns 404

Under **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**. In **Actions → Documentation**, confirm that both build and deploy have completed. A successful build alone does not publish the site. Use the full [project URL](development.md#github-pages), including the repository name.

## Report a problem

Open a [GitHub issue](https://github.com/WEIXUEP/microstrip-quasistatic-impedance/issues) with the complete command, expected and observed behavior, error log, `result.json` if generated, operating system, Python/dependency versions, and Git commit. For solver comparisons, include the geometry and boundary definitions of both models.
