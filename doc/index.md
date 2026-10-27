---
title: Overview
hide:
  - toc
---

<div class="qs-hero" markdown>
<div markdown>

# Microstrip impedance from the cross section.

Compute quasi-TEM impedance with two electrostatic finite-element solves. Define the layers and trace, generate a mesh, and inspect the result in Python.

<div class="qs-actions" markdown>
[Run your first case](quickstart.md){ .md-button .md-button--primary }
[Explore the model](geometry.md){ .md-button }
</div>
</div>
<figure class="qs-figure" markdown>
![Annotated two-layer microstrip: trapezoidal trace at the dielectric interface, finite-width ground, and enclosing air region](microstrip_geometry.svg)
<figcaption>A two-layer cross section with an ideal signal conductor and finite-width ground. Schematic, not to scale.</figcaption>
</figure>
</div>

<div class="qs-method">
<div><strong>Real dielectric</strong><span>Solve for capacitance C with the specified layer permittivities.</span></div>
<div><strong>Vacuum reference</strong><span>Solve the same mesh with all dielectric regions set to εr = 1 to obtain C₀.</span></div>
<div><strong>Quasi-TEM impedance</strong><span>Z₀ = 1 / (c √(C C₀)), with capacitances in F/m and impedance in Ω.</span></div>
</div>

<div class="qs-start" markdown>
<div markdown>

## Start a calculation

Requires Python **3.10+**. Create a [virtual environment](quickstart.md), then install the solver dependencies and run:

```shell
python -m pip install -r requirements.txt
python microstrip_quasistatic.py
```

Read `characteristic_impedance_ohm` in `output/result.json`. The companion `microstrip.msh` contains the generated geometry mesh. All input dimensions use **mil**: 1 mil = 25.4 μm.

Gmsh builds the mesh. scikit-fem assembles the finite-element system, and SciPy solves it. No Palace or other external EM solver is required.

</div>
<div class="qs-reading" markdown>

## Work with the model

<a href="geometry/"><strong>Geometry & boundaries</strong><span>Layer thicknesses, trapezoidal traces, finite ground, and air-box truncation.</span></a>
<a href="cli/"><strong>Command-line reference</strong><span>Every argument, its default, and the two mesh-area controls.</span></a>
<a href="output/"><strong>Understand the output</strong><span>JSON fields, units, mesh contents, and reference-value limitations.</span></a>
<a href="validation/"><strong>Check convergence</strong><span>Vacuum consistency, mesh refinement, domain size, and historical benchmarks.</span></a>

</div>
</div>

<div class="qs-scope" markdown>

## What the model covers

A uniform transmission-line cross section with linear, isotropic dielectrics and ideal conductors, under a quasi-static, quasi-TEM approximation. The outputs are capacitance, inductance, effective permittivity, phase velocity, and characteristic impedance per the [FEM formulation](theory.md).

The finite air box uses a zero-normal-flux outer boundary. Check mesh and domain convergence before relying on the result. Frequency sweeps, losses, dispersion, roughness, skin effect, three-dimensional transitions, and S parameters are outside the current model.

[Source code](https://github.com/WEIXUEP/microstrip-quasistatic-impedance) is available under the [Apache License 2.0](https://github.com/WEIXUEP/microstrip-quasistatic-impedance/blob/main/LICENSE).

</div>
