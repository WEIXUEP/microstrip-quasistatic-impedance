# Output reference

Each run writes `microstrip.msh` and `result.json` and prints the main results. Reusing the same output directory overwrites these files.

## JSON fields

| Field | Unit / type | Meaning |
| --- | --- | --- |
| `geometry` | Object | All `MicrostripGeometry` fields, including dimensions, domain factors, and derived mesh sizes |
| `mesh.vertices` | Integer | FEM vertices after removing unused nodes inside the metal |
| `mesh.triangles` | Integer | FEM triangles outside the metal |
| `mesh.finite_element_order` | 1 or 2 | Potential-space order |
| `mesh.finite_element_dofs` | Integer | All potential degrees of freedom, including fixed ones |
| `capacitance_F_per_m` | F/m | Real-dielectric capacitance C per unit length |
| `vacuum_capacitance_F_per_m` | F/m | Same-geometry, same-mesh vacuum capacitance C0 |
| `effective_permittivity` | Dimensionless | C/C0 |
| `inductance_H_per_m` | H/m | `1/(c² C0)` |
| `phase_velocity_m_per_s` | m/s | `c/sqrt(C/C0)` |
| `characteristic_impedance_ohm` | Ω | `1/(c sqrt(C C0))` |
| `palace_reference_impedance_ohm` | Ω or `null` | Built-in reference; see the matching limitation below |
| `difference_from_reference_ohm` | Ω or `null` | Computed impedance minus the built-in reference |

Length fields under `geometry`, including `mesh_size_trace` and `mesh_size_far`, use mil. Relative permittivities, `substrate_width_factor`, the three `air_padding_*` fields, and both mesh-area factors are dimensionless. See the full [Python field list](development.md#python-api).

!!! warning "The built-in Palace reference matches only the widths"
    When W1=W2=10 mil, the current script inserts the hard-coded value `30.216744231553 Ω`. It does not also match H1, H2, T, Er1, or Er2. Changing those parameters can leave an unrelated reference in the result. Do not automatically treat it as a valid benchmark for your geometry. Both reference fields are `null` for other widths.

## Read and convert results

Convert capacitance to pF/m and inductance to nH/m:

```python
import json
from pathlib import Path

r = json.loads(Path("output/result.json").read_text(encoding="utf-8"))
print(f"C = {r['capacitance_F_per_m'] * 1e12:.3f} pF/m")
print(f"L = {r['inductance_H_per_m'] * 1e9:.3f} nH/m")
print(f"Z0 = {r['characteristic_impedance_ohm']:.6f} ohm")
```

F/m is capacitance **per unit length**, not total capacitance. The model has no line-length parameter. For a uniform segment, multiplying C by length in meters approximates total static capacitance, excluding end effects.

## Mesh-file contents

- Format: **Gmsh MSH 2.2 ASCII**.
- Exported coordinates use **mil**. The meter conversion happens in memory after export and is not written back into the file.
- All Gmsh regions are included, including metal-interior triangles. The solver excludes the metal and removes unused nodes when constructing the FEM connectivity.
- No material or boundary Physical Groups are written. Geometric entity tags are not stable material names.
- Potentials, electric fields, and solved results are not stored in the mesh. Field plots and `.vtu` export are not currently implemented.

Open the `.msh` in Gmsh to inspect geometry and mesh density. Its displayed counts can exceed the FEM counts in JSON because the file still contains metal-interior elements.

## Sanity checks

C, C0, L, and Z0 should be finite and positive. For ordinary materials with Er ≥ 1, expect `1 ≤ εeff ≤ max(Er1, Er2)` and phase velocity no greater than the speed of light in vacuum. Setting Er1=Er2=1 should make εeff approximately 1.

These checks catch obvious problems; they do not establish accuracy. Follow them with [mesh and domain convergence](validation.md).
