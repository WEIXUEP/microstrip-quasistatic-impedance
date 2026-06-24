#!/usr/bin/env python3
"""Pure-Python quasi-static FEM demo for a fixed microstrip cross section.

Gmsh is used only to construct and mesh the geometry. The electrostatic finite
element matrices, boundary conditions, sparse solves, energy integration, and
impedance postprocessing are implemented in this file with NumPy and SciPy.
No Palace executable or Palace output file is required.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import gmsh
import numpy as np
from scipy.constants import c, epsilon_0
from skfem import (
    Basis,
    BilinearForm,
    ElementTriP0,
    ElementTriP1,
    ElementTriP2,
    MeshTri,
    asm,
    condense,
    solve,
)
from skfem.helpers import dot, grad


MIL_TO_M = 25.4e-6


@dataclass(frozen=True)
class MicrostripGeometry:
    """Dimensions in mil and relative dielectric constants."""

    h1: float = 2.97
    h2: float = 3.53
    trace_thickness: float = 1.80
    w1: float = 5.60
    w2: float = 5.60
    er1: float = 4.20
    er2: float = 4.20
    substrate_width_factor: float = 30.0
    air_padding_x_factor: float = 10.0
    air_padding_top_factor: float = 10.0
    air_padding_bottom_factor: float = 2.0
    trace_mesh_area_factor: float = 50.0
    far_mesh_area_factor: float = 400.0
    mesh_size_trace: float = 0.12
    mesh_size_far: float = 3.0

    @property
    def total_height(self) -> float:
        return self.h1 + self.h2

    @property
    def substrate_width(self) -> float:
        return self.substrate_width_factor * self.total_height

    @property
    def air_half_width(self) -> float:
        return 0.5 * self.substrate_width + self.air_padding_x_factor * self.total_height

    @property
    def max_trace_width(self) -> float:
        return max(self.w1, self.w2)

    @property
    def trace_area(self) -> float:
        return 0.5 * (self.w1 + self.w2) * self.trace_thickness

    @property
    def simulation_area(self) -> float:
        width = 2.0 * self.air_half_width
        height = (1.0 + self.air_padding_top_factor + self.air_padding_bottom_factor) * self.total_height
        return width * height


@dataclass
class MeshData:
    points: np.ndarray
    triangles: np.ndarray
    relative_permittivity: np.ndarray
    signal_nodes: np.ndarray
    ground_nodes: np.ndarray


def _surface_kind(bounds: tuple[float, ...], p: MicrostripGeometry) -> str:
    xmin, ymin, _, xmax, ymax, _ = bounds
    # OCC bounding boxes are padded by roughly 1e-7 model units.
    tol = 1.0e-5
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    half_trace = 0.5 * p.max_trace_width
    trace_bottom = p.h1
    trace_top = p.h1 + p.trace_thickness
    is_trace = (
        xmin >= -half_trace - tol
        and xmax <= half_trace + tol
        and ymin >= trace_bottom - tol
        and ymax <= trace_top + tol
    )
    if is_trace:
        return "trace"
    in_substrate = abs(xmid) <= 0.5 * p.substrate_width + tol and -tol <= ymid <= p.total_height + tol
    if not in_substrate:
        return "air"
    return "lower" if ymid < p.h1 else "upper"


def _curve_kind(bounds: tuple[float, ...], p: MicrostripGeometry) -> str | None:
    xmin, ymin, _, xmax, ymax, _ = bounds
    tol = 1.0e-5
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    horizontal = ymax - ymin < tol
    half_trace = 0.5 * p.max_trace_width
    bottom = p.h1
    top = p.h1 + p.trace_thickness
    in_trace_box = (
        xmin >= -half_trace - tol
        and xmax <= half_trace + tol
        and ymin >= bottom - tol
        and ymax <= top + tol
    )
    on_trace = in_trace_box and (abs(ymid - bottom) < tol or abs(ymid - top) < tol or ymax - ymin > tol)
    if on_trace:
        return "signal"
    on_ground = (
        horizontal
        and abs(ymid) < tol
        and xmin >= -0.5 * p.substrate_width - tol
        and xmax <= 0.5 * p.substrate_width + tol
    )
    return "ground" if on_ground else None


def generate_mesh(p: MicrostripGeometry, mesh_path: Path) -> MeshData:
    """Build a first-order triangular mesh and return its FEM connectivity."""

    if p.trace_thickness >= p.h2:
        raise ValueError("trace_thickness must be smaller than h2")

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("pure_python_microstrip")
        h = p.total_height
        air_bottom = -p.air_padding_bottom_factor * h
        air_top = h + p.air_padding_top_factor * h
        half_air = p.air_half_width
        half_sub = 0.5 * p.substrate_width

        air = gmsh.model.occ.addRectangle(-half_air, air_bottom, 0.0, 2.0 * half_air, air_top - air_bottom)
        lower = gmsh.model.occ.addRectangle(-half_sub, 0.0, 0.0, 2.0 * half_sub, p.h1)
        upper = gmsh.model.occ.addRectangle(-half_sub, p.h1, 0.0, 2.0 * half_sub, p.h2)
        trace_bottom = p.h1
        trace_top = p.h1 + p.trace_thickness
        p1 = gmsh.model.occ.addPoint(-0.5 * p.w1, trace_bottom, 0.0)
        p2 = gmsh.model.occ.addPoint(0.5 * p.w1, trace_bottom, 0.0)
        p3 = gmsh.model.occ.addPoint(0.5 * p.w2, trace_top, 0.0)
        p4 = gmsh.model.occ.addPoint(-0.5 * p.w2, trace_top, 0.0)
        l1 = gmsh.model.occ.addLine(p1, p2)
        l2 = gmsh.model.occ.addLine(p2, p3)
        l3 = gmsh.model.occ.addLine(p3, p4)
        l4 = gmsh.model.occ.addLine(p4, p1)
        trace = gmsh.model.occ.addPlaneSurface([gmsh.model.occ.addCurveLoop([l1, l2, l3, l4])])
        gmsh.model.occ.fragment([(2, air), (2, lower), (2, upper), (2, trace)], [])
        gmsh.model.occ.synchronize()

        domain_surfaces: list[tuple[int, str]] = []
        signal_curves: list[int] = []
        ground_curves: list[int] = []
        for _, tag in gmsh.model.getEntities(2):
            kind = _surface_kind(gmsh.model.getBoundingBox(2, tag), p)
            if kind != "trace":
                domain_surfaces.append((tag, kind))
        for _, tag in gmsh.model.getEntities(1):
            kind = _curve_kind(gmsh.model.getBoundingBox(1, tag), p)
            if kind == "signal":
                signal_curves.append(tag)
            elif kind == "ground":
                ground_curves.append(tag)

        if not signal_curves or not ground_curves:
            raise RuntimeError("failed to identify signal or ground boundary")

        gmsh.model.mesh.field.add("Distance", 1)
        gmsh.model.mesh.field.setNumbers(1, "CurvesList", signal_curves + ground_curves)
        gmsh.model.mesh.field.setNumber(1, "Sampling", 150)
        gmsh.model.mesh.field.add("Threshold", 2)
        gmsh.model.mesh.field.setNumber(2, "InField", 1)
        gmsh.model.mesh.field.setNumber(2, "SizeMin", p.mesh_size_trace)
        gmsh.model.mesh.field.setNumber(2, "SizeMax", p.mesh_size_far)
        gmsh.model.mesh.field.setNumber(2, "DistMin", 0.5 * p.trace_thickness)
        gmsh.model.mesh.field.setNumber(2, "DistMax", 8.0 * max(p.h1, p.h2, p.max_trace_width))
        gmsh.model.mesh.field.setAsBackgroundMesh(2)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.model.mesh.generate(2)

        mesh_path.parent.mkdir(parents=True, exist_ok=True)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.option.setNumber("Mesh.Binary", 0)
        gmsh.write(str(mesh_path))

        node_tags, xyz, _ = gmsh.model.mesh.getNodes()
        node_tags = np.asarray(node_tags, dtype=np.int64)
        points_m = np.asarray(xyz, dtype=float).reshape(-1, 3)[:, :2] * MIL_TO_M
        order = np.argsort(node_tags)
        sorted_tags = node_tags[order]

        def local_indices(tags: np.ndarray) -> np.ndarray:
            positions = np.searchsorted(sorted_tags, tags)
            return order[positions]

        all_triangles: list[np.ndarray] = []
        all_er: list[np.ndarray] = []
        er_for_kind = {"air": 1.0, "lower": p.er1, "upper": p.er2}
        for surface_tag, kind in domain_surfaces:
            element_types, _, element_nodes = gmsh.model.mesh.getElements(2, surface_tag)
            for element_type, nodes in zip(element_types, element_nodes):
                _, _, _, node_count, _, _ = gmsh.model.mesh.getElementProperties(element_type)
                if node_count != 3:
                    raise RuntimeError("demo expects first-order triangular elements")
                triangles = local_indices(np.asarray(nodes, dtype=np.int64)).reshape(-1, 3)
                all_triangles.append(triangles)
                all_er.append(np.full(triangles.shape[0], er_for_kind[kind]))
                

        def boundary_nodes(curves: list[int]) -> np.ndarray:
            tags: list[np.ndarray] = []
            for curve in curves:
                curve_tags, _, _ = gmsh.model.mesh.getNodes(1, curve, includeBoundary=True)
                tags.append(np.asarray(curve_tags, dtype=np.int64))
            return np.unique(local_indices(np.unique(np.concatenate(tags))))

        triangles = np.vstack(all_triangles)
        signal_nodes = boundary_nodes(signal_curves)
        ground_nodes = boundary_nodes(ground_curves)

        # Gmsh also meshes the metal surface. Its triangles were deliberately
        # excluded above, so remove the resulting unconnected interior nodes.
        used_nodes = np.unique(triangles)
        old_to_new = np.full(len(points_m), -1, dtype=np.int64)
        old_to_new[used_nodes] = np.arange(len(used_nodes))
        triangles = old_to_new[triangles]
        signal_nodes = old_to_new[np.intersect1d(signal_nodes, used_nodes)]
        ground_nodes = old_to_new[np.intersect1d(ground_nodes, used_nodes)]

        return MeshData(
            points=points_m[used_nodes],
            triangles=triangles,
            relative_permittivity=np.concatenate(all_er),
            signal_nodes=signal_nodes,
            ground_nodes=ground_nodes,
        )
    finally:
        gmsh.finalize()


def solve_electrostatic(
    mesh: MeshData, p: MicrostripGeometry, vacuum: bool, order: int
) -> tuple[np.ndarray, float]:
    """Solve div(epsilon grad(phi)) = 0 and return potential and C' in F/m."""

    fem_mesh = MeshTri(
        np.ascontiguousarray(mesh.points.T), np.ascontiguousarray(mesh.triangles.T)
    )
    element = ElementTriP2() if order == 2 else ElementTriP1()
    basis = Basis(fem_mesh, element)
    element_er = np.ones_like(mesh.relative_permittivity) if vacuum else mesh.relative_permittivity
    material_basis = Basis(fem_mesh, ElementTriP0(), quadrature=basis.quadrature)
    er_field = material_basis.interpolate(element_er)

    @BilinearForm
    def electrostatic(u, v, w):
        return epsilon_0 * w.er * dot(grad(u), grad(v))

    stiffness = asm(electrostatic, basis, er=er_field)
    # Select all P1/P2 degrees of freedom by their physical coordinates. For
    # P2 this includes edge-midpoint DOFs on both the trace and internal ground.
    x, y = basis.doflocs
    tol = 1.0e-10
    trace_bottom = p.h1 * MIL_TO_M
    trace_top = (p.h1 + p.trace_thickness) * MIL_TO_M
    trace_height = p.trace_thickness * MIL_TO_M
    half_bottom = 0.5 * p.w1 * MIL_TO_M
    half_top = 0.5 * p.w2 * MIL_TO_M
    half_substrate = 0.5 * p.substrate_width * MIL_TO_M
    on_trace_horizontal = (
        ((np.abs(y - trace_bottom) < tol) & (x >= -half_bottom - tol) & (x <= half_bottom + tol))
        | ((np.abs(y - trace_top) < tol) & (x >= -half_top - tol) & (x <= half_top + tol))
    )
    y_fraction = np.clip((y - trace_bottom) / trace_height, 0.0, 1.0)
    half_width_at_y = half_bottom + y_fraction * (half_top - half_bottom)
    on_trace_side = (
        np.abs(np.abs(x) - half_width_at_y) < tol
    ) & (y >= trace_bottom - tol) & (y <= trace_top + tol)
    signal_dofs = np.flatnonzero(on_trace_horizontal | on_trace_side)
    ground_dofs = np.flatnonzero(
        (np.abs(y) < tol) & (x >= -half_substrate - tol) & (x <= half_substrate + tol)
    )
    if signal_dofs.size == 0 or ground_dofs.size == 0:
        raise RuntimeError("failed to identify signal or ground finite element DOFs")

    potential = np.zeros(basis.N)
    potential[signal_dofs] = 1.0
    fixed = np.unique(np.concatenate((signal_dofs, ground_dofs)))
    potential = solve(*condense(stiffness, np.zeros(basis.N), x=potential, D=fixed))

    # U' = 0.5 * phi^T K phi and C' = 2 U' / V^2, with V = 1 V.
    capacitance_per_length = float(potential @ (stiffness @ potential))
    return potential, float(capacitance_per_length)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h1", type=float, default=2.97, help="lower dielectric height in mil")
    parser.add_argument("--h2", type=float, default=3.53, help="upper dielectric height in mil")
    parser.add_argument(
        "--trace-thickness",
        type=float,
        default=1.80,
        help="trace thickness in mil",
    )
    parser.add_argument("--w1", type=float, default=10, help="bottom trace width in mil")
    parser.add_argument("--w2", type=float, default=5.60, help="top trace width in mil")
    parser.add_argument("--er1", type=float, default=4.20, help="lower dielectric relative permittivity")
    parser.add_argument("--er2", type=float, default=4.20, help="upper dielectric relative permittivity")
    parser.add_argument(
        "--trace-mesh-area-factor",
        type=float,
        default=50.0,
        help="trace metal area divisor used to derive the minimum mesh size",
    )
    parser.add_argument(
        "--far-mesh-area-factor",
        type=float,
        default=400.0,
        help="simulation-domain area divisor used to derive the far-field mesh size",
    )
    parser.add_argument("--order", type=int, choices=(1, 2), default=2, help="finite element order")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.trace_mesh_area_factor <= 0.0:
        raise ValueError("trace_mesh_area_factor must be positive")
    if args.far_mesh_area_factor <= 0.0:
        raise ValueError("far_mesh_area_factor must be positive")
    p = MicrostripGeometry(
        h1=args.h1,
        h2=args.h2,
        trace_thickness=args.trace_thickness,
        w1=args.w1,
        w2=args.w2,
        er1=args.er1,
        er2=args.er2,
        trace_mesh_area_factor=args.trace_mesh_area_factor,
        far_mesh_area_factor=args.far_mesh_area_factor,
    )
    p = replace(
        p,
        mesh_size_trace=float(np.sqrt(p.trace_area / p.trace_mesh_area_factor)),
        mesh_size_far=float(np.sqrt(p.simulation_area / p.far_mesh_area_factor)),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    mesh = generate_mesh(p, args.output / "microstrip.msh")
    potential, capacitance = solve_electrostatic(mesh, p, vacuum=False, order=args.order)
    _, vacuum_capacitance = solve_electrostatic(mesh, p, vacuum=True, order=args.order)

    epsilon_eff = capacitance / vacuum_capacitance
    inductance = 1.0 / (c**2 * vacuum_capacitance)
    phase_velocity = c / np.sqrt(epsilon_eff)
    impedance = 1.0 / (c * np.sqrt(capacitance * vacuum_capacitance))
    reference = 30.216744231553 if abs(p.w1 - 10.0) < 1.0e-12 and abs(p.w2 - 10.0) < 1.0e-12 else None

    result = {
        "geometry": asdict(p),
        "mesh": {
            "vertices": len(mesh.points),
            "triangles": len(mesh.triangles),
            "finite_element_order": args.order,
            "finite_element_dofs": len(potential),
        },
        "capacitance_F_per_m": capacitance,
        "vacuum_capacitance_F_per_m": vacuum_capacitance,
        "effective_permittivity": epsilon_eff,
        "inductance_H_per_m": inductance,
        "phase_velocity_m_per_s": phase_velocity,
        "characteristic_impedance_ohm": impedance,
        "palace_reference_impedance_ohm": reference,
        "difference_from_reference_ohm": None if reference is None else impedance - reference,
    }
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")

    print("Pure-Python quasi-static microstrip FEM")
    print(f"  mesh                  : {len(mesh.points)} vertices, {len(mesh.triangles)} triangles")
    print(f"  finite element space  : P{args.order}, {len(potential)} DOFs")
    print(f"  C                     : {capacitance:.12e} F/m")
    print(f"  C0                    : {vacuum_capacitance:.12e} F/m")
    print(f"  effective permittivity: {epsilon_eff:.12f}")
    print(f"  phase velocity        : {phase_velocity:.12e} m/s")
    print(f"  inductance            : {inductance:.12e} H/m")
    print(f"  Z0                    : {impedance:.12f} Ohm")
    if reference is not None:
        print(f"  Palace reference      : {reference:.12f} Ohm")
        print(f"  difference            : {impedance - reference:+.12f} Ohm")
    print(f"  result                : {args.output / 'result.json'}")


if __name__ == "__main__":
    main()
