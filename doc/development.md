# 开发与文档发布

## 仓库结构

```text
microstrip_quasistatic.py   几何、网格、有限元、CLI 与 JSON 输出
requirements.txt           计算运行依赖
requirements-docs.txt      文档构建依赖
README.md                  英文仓库入口
README.zh-CN.md            中文仓库入口
mkdocs.yml                 网站主题、搜索与导航配置
doc/                       Markdown 文档和 SVG 几何示意图
.github/workflows/docs.yml 文档检查与 GitHub Pages 发布
```

`.venv/`、`output/` 和 `site/` 是本地环境或生成产物，不应提交到源码仓库。

## Python API {#python-api}

模块可以直接导入，导入时不会自动执行 `main()`。主要接口如下：

| 接口 | 输入 | 返回或作用 |
| --- | --- | --- |
| `MicrostripGeometry(...)` | 长度（mil）、介电常数、尺寸和网格因子 | 冻结的数据类 |
| `generate_mesh(p, mesh_path)` | 几何对象、输出 `Path` | 写 `.msh`，返回 `MeshData` |
| `solve_electrostatic(mesh, p, vacuum, order)` | 网格、同一几何、是否真空、阶数 1/2 | `(potential, capacitance_per_length)` |

`MeshData.points` 为 `(N, 2)` 的米坐标，`triangles` 为 `(M, 3)` 的零起始顶点索引，`relative_permittivity` 长度为 M。`signal_nodes` 和 `ground_nodes` 保存顶点索引；求解器通过自由度坐标重新识别固定电位位置，以覆盖 P2 边中点。

`potential` 是有限元自由度顺序的电位数组；P2 时长度一般大于顶点数，不能当成 Gmsh 原始节点顺序的数据。电容单位为 F/m。

### 类字段默认值

| 字段 | 默认值 | 单位 |
| --- | ---: | --- |
| `h1`, `h2` | 2.97, 3.53 | mil |
| `w1`, `w2` | **5.60, 5.60** | mil |
| `trace_thickness` | 1.80 | mil |
| `er1`, `er2` | 4.20, 4.20 | 无量纲 |
| `substrate_width_factor` | 30.0 | 无量纲 |
| `air_padding_x_factor` | 10.0 | 无量纲 |
| `air_padding_top_factor` | 10.0 | 无量纲 |
| `air_padding_bottom_factor` | 2.0 | 无量纲 |
| `trace_mesh_area_factor` | 50.0 | 无量纲 |
| `far_mesh_area_factor` | 400.0 | 无量纲 |
| `mesh_size_trace` | 0.12 | mil |
| `mesh_size_far` | 3.0 | mil |

类本身不根据面积因子自动重算网格尺寸，`generate_mesh()` 直接使用 `mesh_size_trace` / `mesh_size_far`。CLI 的 `main()` 才会通过 `dataclasses.replace()` 将尺寸换算为[面积公式](cli.md)的结果。使用 API 时要明确选择手动尺寸还是面积因子推导。

### 最小调用示例

在项目根目录保存为独立脚本并使用虚拟环境运行：

```python
from dataclasses import replace
from math import sqrt
from pathlib import Path
from scipy.constants import c
from microstrip_quasistatic import (
    MicrostripGeometry, generate_mesh, solve_electrostatic,
)

p = MicrostripGeometry(w1=10.0, w2=5.6)
p = replace(
    p,
    mesh_size_trace=sqrt(p.trace_area / p.trace_mesh_area_factor),
    mesh_size_far=sqrt(p.simulation_area / p.far_mesh_area_factor),
)
mesh = generate_mesh(p, Path("output/api/microstrip.msh"))
potential, capacitance = solve_electrostatic(mesh, p, vacuum=False, order=2)
_, vacuum_capacitance = solve_electrostatic(mesh, p, vacuum=True, order=2)
impedance = 1.0 / (c * sqrt(capacitance * vacuum_capacitance))
print(f"Z0 = {impedance:.6f} ohm")
```

`generate_mesh()` 自行初始化和结束 Gmsh 会话，不要嵌套在另一个自行管理的 Gmsh 会话中调用。

## 本地预览 HTML

在项目根目录安装文档依赖；不需要安装计算依赖或运行求解器：

```shell
python -m pip install -r requirements-docs.txt
python -m mkdocs serve
```

浏览器打开终端显示的地址，通常为 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)。修改 Markdown 后预览会刷新。Windows 可用 `.\.venv\Scripts\python.exe` 替换 `python`。

生成可部署的静态 HTML：

```shell
python -m mkdocs build --strict
```

产物位于 `site/`。建议通过 HTTP 服务预览，保证目录链接和搜索正常工作：

```shell
python -m http.server 8000 --directory site
```

## GitHub Pages 发布 {#github-pages}

本站目标网址：

**[https://weixuep.github.io/microstrip-quasistatic-impedance/](https://weixuep.github.io/microstrip-quasistatic-impedance/)**

首次配置由仓库管理员完成：

1. 将文档源文件和 `.github/workflows/docs.yml` 提交到 `main`。
2. 在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. 在 **Actions → Documentation → Run workflow** 选择 `main` 并运行，或推送一次文档改动。
4. 等待 build 与 deploy 均成功，访问上述项目网址。

工作流不需要个人访问令牌或额外 Secret；部署使用 GitHub 的 `GITHUB_TOKEN` 和 OIDC，写权限只授予 deploy 作业。若仓库环境设置要求人工审核，需要在 GitHub 上完成相应审核。

后续修改 `doc/`、`mkdocs.yml`、文档依赖或工作流，推送到 `main` 后会自动发布。Pull Request 只检查和构建，并上传 `documentation-html` 供审阅。手动触发也支持重新发布；非 `main` 分支不会部署。

迁移或 fork 仓库时，修改 `mkdocs.yml` 的 `site_url`、`repo_url`、`repo_name`，同步更新 README 和本页中的网站链接。若默认分支改变，还要更新工作流分支条件和 `edit_uri`。

## 维护检查

文档修改后先运行严格构建，修正内部文件链接、导航和配置问题。增加页面时同步 `mkdocs.yml` 的 `nav`。严格构建不会验证外部站点是否在线，发布后仍需打开首页、侧栏页面和搜索检查。

修改计算实现时，至少检查默认运行、全真空一致性和相关收敛结果。参数、单位、默认值、输出字段和边界行为变化时，同步更新相应文档。历史对照数据需要保留来源说明，新的精度结论应附可复现设置。
