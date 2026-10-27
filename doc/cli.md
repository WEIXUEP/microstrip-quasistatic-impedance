# 命令行参数

```shell
python microstrip_quasistatic.py --help
```

以下默认值来自 `parse_args()`，对应直接运行脚本的行为。长度单位均为 **mil**，介电常数和面积因子无量纲。

## 完整参数表

| 参数 | 默认值 | 含义 |
| --- | ---: | --- |
| `--h1` | 2.97 | 下层介质厚度 |
| `--h2` | 3.53 | 上层介质厚度，包含信号线厚度 |
| `--er1` | 4.20 | 下层相对介电常数 |
| `--er2` | 4.20 | 上层相对介电常数 |
| `--w1` | **10.00** | 信号线底部宽度 |
| `--w2` | 5.60 | 信号线顶部宽度 |
| `--trace-thickness` | 1.80 | 信号线厚度，必须小于 H2 |
| `--trace-mesh-area-factor` | 50.0 | 走线面积除数，用于推导近导体网格尺寸 |
| `--far-mesh-area-factor` | 400.0 | 计算域面积除数，用于推导远处网格尺寸 |
| `--order` | 2 | 有限元阶数，只能为 1 或 2 |
| `--output` | 脚本旁的 `output/` | 输出目录，可使用绝对路径 |
| `-h`, `--help` | — | 显示帮助并退出 |

!!! note "CLI 与 Python 类默认值有区别"
    `MicrostripGeometry()` 的 `w1` 默认是 **5.60**，CLI 的 `--w1` 默认是 **10.00**。直接构造类得到矩形走线，直接运行脚本得到梯形走线。复现实验时请显式填写关键尺寸，不要混用两套默认值。

## 网格面积因子

CLI 在生成网格前计算：

```text
trace_area = (W1 + W2) × T / 2
simulation_area = 空气盒总宽 × 空气盒总高
mesh_size_trace = sqrt(trace_area / trace_mesh_area_factor)
mesh_size_far = sqrt(simulation_area / far_mesh_area_factor)
```

面积使用 mil²，推导得到的尺寸使用 mil。因子越大，目标网格越细；它们不是单元数量，也不能直接解释为误差容限。因子乘以 4，会将对应目标尺寸减半。

Gmsh 的距离场同时参考信号线和地的曲线，在近处和远处目标尺寸之间过渡。实际单元数还取决于几何、距离场和网格算法。

## 有限元阶数与网格阶数

`--order 1` 使用三角形 P1 电位，`--order 2` 使用 P2 电位。**两种情况导出的 Gmsh 网格都是一阶三角形**；P2 的边中点自由度由 scikit-fem 创建，不会让 `.msh` 变成二阶网格。

## 常用命令

矩形走线：

```shell
python microstrip_quasistatic.py --w1 10 --w2 10 --output output/rectangular
```

保持几何不变，加密网格：

```shell
python microstrip_quasistatic.py --trace-mesh-area-factor 200 --far-mesh-area-factor 1600 --output output/refined
```

真空一致性检查：

```shell
python microstrip_quasistatic.py --er1 1 --er2 1 --output output/vacuum
```

更多收敛步骤和对照案例见[验证文档](validation.md)。
