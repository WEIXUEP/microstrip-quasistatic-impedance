# Quasi-static FEM

The solver uses two electrostatic capacitance calculations to recover lossless quasi-TEM transmission-line parameters.

## Two electrostatic problems

For a uniform cross section with signal-to-ground voltage V, the potential satisfies:

```text
∇ · (ε ∇φ) = 0
E = −∇φ
ε = ε0 εr
```

The signal is fixed at 1 V and the ground at 0 V. Two problems are solved on the same discrete mesh:

1. **Real dielectric:** air has εr=1, and the layers use Er1 and Er2. This gives C.
2. **Vacuum reference:** all nonmetal regions use εr=1. This gives C0.

The vacuum solve retains the metal geometry, ground, and air box. Only the permittivity changes. A shared mesh keeps the geometric discretization consistent.

## Weak form and discretization

Integrating with a test function v that vanishes on the fixed-potential boundaries gives:

```text
∫Ω ε ∇φ · ∇v dA = 0
Kij = ∫Ω ε ∇Ni · ∇Nj dA
```

Each triangle has a constant relative permittivity, passed to the bilinear form through an `ElementTriP0` material field. The potential uses `ElementTriP1` or `ElementTriP2`. scikit-fem assembles the sparse matrix, condenses fixed degrees of freedom, and delegates the solve to SciPy.

The air-box exterior has the natural zero-normal-displacement condition described under [geometry and boundaries](geometry.md). With P2, conductor potentials are fixed at both vertices and edge midpoints.

## Capacitance from energy

Electric-field energy per unit propagation length is:

```text
U′ = 1/2 ∫Ω ε |∇φ|² dA = 1/2 φᵀ K φ
C′ = 2U′ / V²
```

With V=1 V, the numerical value of `φᵀ K φ` directly gives capacitance per unit length. FEM coordinates are in meters, so the result is in F/m. Energy is evaluated with the complete potential vector and the original stiffness matrix.

## Quasi-TEM parameters

For nonmagnetic media and ideal conductors under the quasi-TEM approximation:

```text
εeff = C / C0
L = 1 / (c² C0)
vp = 1 / sqrt(L C) = c / sqrt(εeff)
Z0 = sqrt(L / C) = 1 / (c sqrt(C C0))
```

C and C0 use F/m; L uses H/m; vp uses m/s; Z0 uses Ω. The constants c and ε0 come from `scipy.constants`.

Effective permittivity describes the whole cross section. It is not the arithmetic average of the layer permittivities: field distribution through air and both dielectric layers determines it.

## Error sources and scope

Important error sources are mesh discretization, rapidly varying fields near sharp conductor corners, finite substrate and ground width, and air-box truncation. Higher-order elements can help, but do not replace [convergence checks](validation.md).

The model has no frequency variable. It applies where the quasi-static and quasi-TEM assumptions are appropriate. It does not compute conductor or dielectric loss, dispersion, radiation, higher-order modes, or S parameters for three-dimensional structures.

## Implementation map

| Step | Code |
| --- | --- |
| Inputs and derived dimensions | `MicrostripGeometry` |
| Geometry fragmentation, distance-field mesh, and SI conversion | `generate_mesh()` |
| Material field, stiffness matrix, boundary DOFs, and energy | `solve_electrostatic()` |
| Mesh-factor conversion, two solves, quasi-TEM parameters, and JSON | `main()` |

Further reading: [scikit-fem documentation](https://scikit-fem.readthedocs.io/) and the [Gmsh reference manual](https://gmsh.info/doc/texinfo/).
