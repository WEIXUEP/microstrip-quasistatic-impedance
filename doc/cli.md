# Command-line reference

```shell
python microstrip_quasistatic.py --help
```

The defaults below come from `parse_args()` and describe direct script execution. All lengths use **mil**. Relative permittivities and area factors are dimensionless.

## All options

| Option | Default | Description |
| --- | ---: | --- |
| `--h1` | 2.97 | Lower dielectric thickness |
| `--h2` | 3.53 | Upper dielectric thickness, including the trace |
| `--er1` | 4.20 | Lower relative permittivity |
| `--er2` | 4.20 | Upper relative permittivity |
| `--w1` | **10.00** | Bottom trace width |
| `--w2` | 5.60 | Top trace width |
| `--trace-thickness` | 1.80 | Trace thickness; must be less than H2 |
| `--trace-mesh-area-factor` | 50.0 | Trace-area divisor used to derive the near-conductor size |
| `--far-mesh-area-factor` | 400.0 | Domain-area divisor used to derive the far-field size |
| `--order` | 2 | Potential-space order: 1 or 2 |
| `--output` | `output/` beside the script | Output directory; absolute paths are accepted |
| `-h`, `--help` | — | Show help and exit |

!!! note "CLI and Python defaults differ"
    `MicrostripGeometry()` defaults to **w1=5.60**, whereas the CLI defaults to **w1=10.00**. Constructing the class directly gives a rectangular trace; running the script without arguments gives a trapezoid. Specify important dimensions explicitly when reproducing a calculation.

## Mesh-area factors

Before generating the mesh, the CLI calculates:

```text
trace_area = (W1 + W2) × T / 2
simulation_area = total air-box width × total air-box height
mesh_size_trace = sqrt(trace_area / trace_mesh_area_factor)
mesh_size_far = sqrt(simulation_area / far_mesh_area_factor)
```

Areas use mil² and derived sizes use mil. Larger factors produce smaller target sizes. These factors are neither element counts nor error tolerances. Multiplying a factor by four halves its target size.

The Gmsh distance field references both signal and ground curves and transitions between the near and far target sizes. Actual element counts also depend on geometry, the distance field, and the meshing algorithm.

## FEM order versus mesh order

`--order 1` uses triangular P1 potentials; `--order 2` uses P2 potentials. **The exported Gmsh mesh uses first-order triangles in both cases.** scikit-fem creates the P2 edge-midpoint degrees of freedom internally; selecting P2 does not make the `.msh` a second-order mesh.

## Common commands

A rectangular trace:

```shell
python microstrip_quasistatic.py --w1 10 --w2 10 --output output/rectangular
```

Refine the mesh while keeping the geometry fixed:

```shell
python microstrip_quasistatic.py --trace-mesh-area-factor 200 --far-mesh-area-factor 1600 --output output/refined
```

Check vacuum consistency:

```shell
python microstrip_quasistatic.py --er1 1 --er2 1 --output output/vacuum
```

See [convergence and benchmarks](validation.md) for systematic checks.
