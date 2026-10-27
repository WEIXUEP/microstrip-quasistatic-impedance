# 输出文件与结果

每次运行写出 `microstrip.msh` 和 `result.json`，并在终端显示主要结果。同一目录中的同名文件会被覆盖。

## result.json 字段

| 字段 | 单位 / 类型 | 含义 |
| --- | --- | --- |
| `geometry` | 对象 | `MicrostripGeometry` 全部字段，包含输入、计算域因子和推导网格尺寸 |
| `mesh.vertices` | 整数 | 排除金属内部孤立节点后的 FEM 网格顶点数 |
| `mesh.triangles` | 整数 | 非金属区域的 FEM 三角形数 |
| `mesh.finite_element_order` | 1 或 2 | 电位有限元阶数 |
| `mesh.finite_element_dofs` | 整数 | 电位自由度总数，包含固定电位自由度 |
| `capacitance_F_per_m` | F/m | 实际介质单位长度电容 C |
| `vacuum_capacitance_F_per_m` | F/m | 同一几何、同一网格全部改为真空时的 C0 |
| `effective_permittivity` | 无量纲 | C/C0 |
| `inductance_H_per_m` | H/m | `1/(c² C0)` |
| `phase_velocity_m_per_s` | m/s | `c/sqrt(C/C0)` |
| `characteristic_impedance_ohm` | Ω | `1/(c sqrt(C C0))` |
| `palace_reference_impedance_ohm` | Ω 或 `null` | 源码内置参考值，见下文限制 |
| `difference_from_reference_ohm` | Ω 或 `null` | 当前阻抗减去内置参考值 |

`geometry` 中长度字段（包括 `mesh_size_trace`、`mesh_size_far`）均为 mil。两个相对介电常数、`substrate_width_factor`、三个 `air_padding_*` 字段和两个网格面积因子为无量纲；字段完整列表见[Python API](development.md#python-api)。

!!! warning "内置 Palace 参考值的匹配条件有限"
    当前程序仅在 W1=W2=10 mil 时填入硬编码参考值 `30.216744231553 Ω`。它没有同时核对 H1、H2、T、Er1 或 Er2，因此其他参数改变后仍可能出现这一数值。不能将该字段自动视为当前几何的正确基准；其他线宽时两个参考字段均为 `null`。

## 读取并换算为 pF/m 与 nH/m

```python
import json
from pathlib import Path

r = json.loads(Path("output/result.json").read_text(encoding="utf-8"))
print(f"C = {r['capacitance_F_per_m'] * 1e12:.3f} pF/m")
print(f"L = {r['inductance_H_per_m'] * 1e9:.3f} nH/m")
print(f"Z0 = {r['characteristic_impedance_ohm']:.6f} Ω")
```

不要将 F/m 误读为总电容。这里没有线长参数；均匀线段的静态总电容近似为 C 乘以长度（米），不含端部效应。

## microstrip.msh 的内容

- 格式为 **Gmsh MSH 2.2 ASCII**。
- 导出坐标使用 **mil**。FEM 求解使用的米坐标是导出后的内存转换，不会回写 `.msh`。
- 包含 Gmsh 生成的所有区域，包括金属内部三角形；求解器在组装 FEM 网格时才排除金属区域并移除未使用节点。
- 当前未写入材料或边界的 Physical Groups。文件中的几何实体标签不等于稳定的材料名称。
- 文件不包含电位、电场或求解结果；当前没有 `.vtu` / 场图导出功能。

可用 Gmsh 桌面程序打开 `.msh` 查看几何和网格。由于保留了金属区域，Gmsh 显示的网格计数可能大于 JSON 中的 FEM 网格计数。

## 结果合理性检查

C、C0、L 和 Z0 应为有限正数。普通 Er ≥ 1 的材料下，通常应有 `1 ≤ εeff ≤ max(Er1, Er2)`，且相速度不超过真空光速。Er1=Er2=1 时，两次问题相同，εeff 应接近 1。

这些检查用于发现明显异常，不是精度证明；进一步做[网格和计算域收敛](validation.md)。
