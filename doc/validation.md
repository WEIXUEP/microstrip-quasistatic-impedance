# 收敛与对照案例

## 建议验证顺序

1. 核对尺寸、单位、材料和边界模型。
2. 用全真空介质检查双求解和单位换算。
3. 保持几何不变，逐步加密网格并比较 P1/P2。
4. 扩大空气盒、基板和地，区分截断误差与有限结构差异。
5. 最后与相同截面定义的解析近似或其他求解器比较。

## 真空一致性

```shell
python microstrip_quasistatic.py --er1 1 --er2 1 --output output/vacuum
```

此时两次静电问题完全相同，应有 `C ≈ C0`、`εeff ≈ 1`、`vp ≈ c`。这只能验证一致性；两个相同问题也可能共享相同的模型或离散误差。

## 参考运行结果

以下为求解器源码提交 `16f7366`、Python 3.11.17、Gmsh 4.15.2、NumPy 2.4.6、SciPy 1.17.1、scikit-fem 12.0.2 环境中的实测结果，使用默认网格因子 50/400 和 P2。不同依赖版本可能产生数值末位差异。

| 输入案例 | FEM 顶点数 | FEM 三角形数 | 自由度数 | Z0 / Ω | εeff |
| --- | ---: | ---: | ---: | ---: | ---: |
| CLI 默认几何 | 10366 | 20471 | 41203 | 31.55849811 | 3.81678467 |
| 默认几何，Er1=Er2=1 | 10366 | 20471 | 41203 | 61.65455342 | 1.00000000 |
| [快速开始中的自定义案例](quickstart.md#custom-case) | 23377 | 46154 | 92908 | 16.37577408 | 3.46987271 |

默认几何的 C 为 `2.064960745030e-10 F/m`，C0 为 `5.410210223165e-11 F/m`。这些结果用于核对安装和输入，仍需按应用要求检查收敛。

## 网格收敛

以下脚本在项目根目录运行，使用当前 Python 解释器启动三个加密级别，显式固定几何，并打印相邻级别的阻抗变化：

```python
import json
import subprocess
import sys
from pathlib import Path

previous = None
for factor in (50, 100, 200):
    output = Path("output") / f"convergence-{factor}"
    subprocess.run([
        sys.executable, "microstrip_quasistatic.py",
        "--h1", "2.97", "--h2", "3.53",
        "--er1", "4.2", "--er2", "4.2",
        "--w1", "10", "--w2", "5.6", "--trace-thickness", "1.8",
        "--order", "2",
        "--trace-mesh-area-factor", str(factor),
        "--far-mesh-area-factor", str(8 * factor),
        "--output", str(output),
    ], check=True)
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    z = result["characteristic_impedance_ohm"]
    change = None if previous is None else 100 * abs(z - previous) / abs(z)
    print(f"factor={factor}, Z0={z:.8f} ohm, change_percent={change}")
    previous = z
```

同时查看 C、C0、εeff 和自由度数，避免只看阻抗时掩盖两个电容误差的抵消。可另外固定面积因子，分别用 `--order 1` 和 `--order 2` 比较。最终阈值由用途决定，例如相邻加密结果小于 0.1% 可作为项目自定标准，但不代表绝对误差必然小于 0.1%。

面积因子加密会增加计算量和内存占用；远处和近导体因子也可以分开调节，以判断主要误差来源。

## 计算域收敛 {#domain-convergence}

当前 CLI 不暴露空气盒或基板尺寸因子，可通过 Python API 调整。下面只扩大空气盒，保持基板、地以及目标网格尺寸不变，从而更直接地观察外边界截断影响：

```python
from dataclasses import replace
from pathlib import Path
from math import sqrt
from scipy.constants import c
from microstrip_quasistatic import (
    MicrostripGeometry, generate_mesh, solve_electrostatic,
)

base = MicrostripGeometry(w1=10.0, w2=5.6)
base = replace(
    base,
    mesh_size_trace=sqrt(base.trace_area / base.trace_mesh_area_factor),
    mesh_size_far=sqrt(base.simulation_area / base.far_mesh_area_factor),
)
for scale in (1.0, 1.5, 2.0):
    p = replace(
        base,
        air_padding_x_factor=base.air_padding_x_factor * scale,
        air_padding_top_factor=base.air_padding_top_factor * scale,
        air_padding_bottom_factor=base.air_padding_bottom_factor * scale,
    )
    mesh = generate_mesh(p, Path(f"output/domain-{scale}/microstrip.msh"))
    _, capacitance = solve_electrostatic(mesh, p, vacuum=False, order=2)
    _, vacuum_capacitance = solve_electrostatic(mesh, p, vacuum=True, order=2)
    impedance = 1.0 / (c * sqrt(capacitance * vacuum_capacitance))
    print(scale, impedance)
```

这里故意保留 `base` 的网格尺寸，不随空气盒面积重新变粗。增大 `substrate_width_factor` 则同时改变介质宽度和地宽，研究的是另一类有限尺寸影响；它还会改变空气盒宽度，需要分别解释。

## Polar SI9000 历史对照

下表保留原 README 的历史对照数据。尺寸单位为 mil，阻抗单位为 Ω。差值定义为 `Python − Polar`，相对差值为 `abs(Python − Polar) / Polar × 100%`。

| 案例 | H1 | Er1 | H2 | Er2 | W1 | W2 | T | Python FEM Z0 | Polar SI9000 Z0 | 差值 | 相对差值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 10.0000 | 4.2000 | 3.5300 | 4.2000 | 10.0000 | 5.6000 | 1.8000 | 64.140182488122 | 63.98 | +0.160182488122 | 0.2504% |
| 2 | 10.0000 | 9.6000 | 20.0000 | 2.2000 | 20.0000 | 10.0000 | 5.0000 | 31.435874124034 | 31.49 | −0.054125875966 | 0.1719% |
| 3 | 20.0000 | 3.6600 | 20.0000 | 2.2000 | 50.0000 | 30.0000 | 4.0000 | 43.290042581624 | 43.28 | +0.010042581624 | 0.0232% |
| 4 | 5.0000 | 3.6600 | 5.0000 | 4.2000 | 20.0000 | 50.0000 | 1.0000 | 16.375774087632 | 16.26 | +0.115774087632 | 0.7120% |
| 5 | 5.0000 | 3.6600 | 5.0000 | 4.2000 | 1.0000 | 1.0000 | 1.0000 | 91.810012129350 | 91.73 | +0.080012129350 | 0.0872% |

上述五例最大历史相对差值为约 **0.72%**。原始记录没有提供完整的依赖版本、网格收敛过程或 Polar 模型设置；这些数值是历史对照，不能当作跨版本精确回归值，也不构成所有几何的精度保证。

重算案例 1：

```shell
python microstrip_quasistatic.py --h1 10 --h2 3.53 --er1 4.2 --er2 4.2 --w1 10 --w2 5.6 --trace-thickness 1.8 --order 2 --output output/polar-case-1
```

## 保存可复现记录

每组结果建议保存输入命令、`result.json`、`.msh`、Git 提交号、Python 版本和依赖清单：

```shell
git rev-parse HEAD
python --version
python -m pip freeze > output/environment.txt
```

对外部求解器还要记录截面类型、地/基板是否有限宽、边界距离、导体厚度与梯形方向、材料定义及收敛设置。
