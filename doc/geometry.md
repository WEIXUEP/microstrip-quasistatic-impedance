# Geometry & boundaries

The model is a two-dimensional cross section in the x–y plane. Propagation is perpendicular to that plane.

![Two-layer microstrip cross section with H1, H2, W1, W2 and trace thickness T](microstrip_geometry.svg)

*Not to scale. The ground is a zero-thickness equipotential line; its drawn thickness is only a visual aid.*

## Coordinates and units

All input lengths, geometry properties, and target mesh sizes use **mil**. Gmsh constructs and exports the geometry in mil coordinates. Before FEM assembly, node coordinates are multiplied by `25.4e-6` to convert them to meters.

| Object | Coordinates or extent | Material / potential |
| --- | --- | --- |
| Lower dielectric | `−Ws/2 ≤ x ≤ Ws/2`, `0 ≤ y ≤ H1` | Relative permittivity Er1 |
| Upper dielectric | `−Ws/2 ≤ x ≤ Ws/2`, `H1 ≤ y ≤ H1+H2`, excluding the trace | Relative permittivity Er2 |
| Bottom of trace | `y = H1`, width W1 | 1 V |
| Top of trace | `y = H1+T`, width W2 | 1 V |
| Trace sides | Straight lines connecting the top and bottom | 1 V |
| Finite ground | `y = 0`, `−Ws/2 ≤ x ≤ Ws/2` | 0 V |
| Air | Inside the enclosing box, outside dielectrics and metal | Relative permittivity 1 |

The bottom of the signal trace sits on the dielectric interface. Its thickness extends into the upper dielectric. **H2 includes T**, so the dielectric thickness above the trace is `H2 − T`.

W1 and W2 are full widths, centered at x=0. Equal widths produce a rectangle; unequal widths produce a trapezoid. Either width can be the larger one.

## Valid inputs

- H1, H2, W1, W2, and T must be positive, with `T < H2`.
- Relative permittivities must be physically meaningful positive values; ordinary dielectrics typically use Er ≥ 1.
- The trace must fit within the substrate: `max(W1, W2) < Ws`.
- Both mesh-area factors must be positive.

The current CLI explicitly checks only the area factors, T < H2, and the finite-element order. Other constraints are the user's responsibility. Negative lengths, zero widths, or invalid materials can fail during meshing or solving.

## Substrate and air-box size

Let `H = H1 + H2`. The default dimensions are:

```text
Ws = substrate_width_factor × H = 30H
Air-box half-width = Ws/2 + air_padding_x_factor × H = 25H
Air-box bottom y = −air_padding_bottom_factor × H = −2H
Air-box top y = H + air_padding_top_factor × H = 11H
Total air-box width = 50H
Total air-box height = 13H
```

These factors are Python fields in `MicrostripGeometry`; the CLI does not expose them. See the [domain-convergence example](validation.md#domain-convergence) to change them.

## Boundary conditions

All signal-trace boundaries are held at 1 V. The finite ground is held at 0 V. The ground lies inside the air box, with air below it; the entire bottom of the box is not grounded.

No Dirichlet condition is applied to the outside of the air box. The weak formulation therefore uses the natural condition:

```text
n · (ε ∇φ) = 0
```

This means zero normal electric-displacement flux. It is a finite-domain truncation, so enlarge the box to assess its influence.

Gmsh fragmentation creates a conforming mesh at dielectric interfaces. A continuous potential space and piecewise dielectric coefficients handle the interface conditions in the weak form. Metal interiors are excluded from the electrostatic solve, although their triangles remain in the exported `.msh`; see the [output reference](output.md).
