# Desktop calculator

The optional PySide6 desktop interface runs the same Python FEM solver as the
command line. All interface labels are in English; dimensions use mil
(`1 mil = 25.4 µm`).

## Install and launch

From the project directory, using Python 3.10 or newer:

```shell
python -m pip install -r requirements-gui.txt
python microstrip_gui.py
```

On Windows, use `.\.venv\Scripts\python.exe` relative to the project directory
when the virtual environment is not activated. On Linux or macOS, use
`.venv/bin/python`. Run the script in Spyder with the interpreter configured to
the environment where the requirements were installed. PySide6 is a Qt GUI
library; Spyder is an optional Python development environment.

## Calculate and save

Enter trace widths, thickness, layer heights and relative permittivities.
The defaults match the command-line defaults. Under **Mesh**, select P1 or P2
and adjust the area factors. The trace thickness must be smaller than H2.

Click **Calculate**. The solver runs in a separate process so the window stays
responsive; **Cancel** stops an active calculation. When it completes, save the
JSON result or Gmsh mesh using the buttons in the results panel. Temporary
results are removed when the window closes, so save anything you need to keep.

The reported capacitances, impedance, effective permittivity, inductance, and
phase velocity have the same definitions as the [CLI output](output.md). Check
[mesh and domain convergence](validation.md) before using a result as an
engineering reference. This model does not include frequency-dependent loss or
full-wave effects.
