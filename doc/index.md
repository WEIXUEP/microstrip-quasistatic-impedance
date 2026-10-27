# 微带线准静态阻抗计算

这个项目用二维静电有限元计算微带线横截面的单位长度电容，再通过真实介质和真空参考两次求解，得到准 TEM 特性阻抗、有效介电常数、等效电感和相速度。

几何和网格由 **Gmsh Python API** 生成，有限元由 **scikit-fem** 组装并调用 **SciPy** 求解。运行不需要 Palace 或其他外部电磁求解器。

![双层介质微带线横截面，含梯形信号线、有限宽地和空气区域](microstrip_geometry.svg)

*示意图不按比例绘制；信号线底面位于两层介质界面，地在计算中是零厚度的有限宽等势线。*

## 从这里开始

| 你的目标 | 阅读内容 |
| --- | --- |
| 第一次运行，获得一个阻抗结果 | [安装与快速开始](quickstart.md) |
| 确认 H1、H2、W1、W2 和 T 的含义 | [几何、材料与边界](geometry.md) |
| 查找所有参数和默认值 | [命令行参数](cli.md) |
| 读取 JSON 或在 Gmsh 中查看网格 | [输出文件与结果](output.md) |
| 理解电容如何转换成阻抗 | [准静态 FEM 原理](theory.md) |
| 判断网格是否足够细、对比 SI9000 | [收敛与对照案例](validation.md) |
| 维护代码或发布本文档网站 | [开发与文档发布](development.md) |

## 最短运行路径

需要 Python 3.10 或更新版本。先在项目目录创建虚拟环境，详细的 Windows、Linux/macOS 命令见[快速开始](quickstart.md)。安装依赖后运行：

```shell
python -m pip install -r requirements.txt
python microstrip_quasistatic.py
```

默认在脚本旁的 `output/` 下生成 `microstrip.msh` 和 `result.json`。阻抗字段为 `characteristic_impedance_ohm`，单位是 Ω。所有命令行几何长度使用 **mil**，`1 mil = 25.4 μm`。

## 模型适用范围

模型用于沿传播方向均匀、可用准 TEM 近似的传输线横截面。材料是线性、各向同性介质，金属作为理想等势导体处理。当前程序不计算频率扫描、损耗、色散、粗糙度、趋肤效应、三维过渡或 S 参数。

空气盒是有限计算域，地也是有限宽度。使用结果前应做[网格与计算域收敛检查](validation.md)，尤其不要把空气盒边界当作精确开放边界。

## 源码与许可

源码：[WEIXUEP/microstrip-quasistatic-impedance](https://github.com/WEIXUEP/microstrip-quasistatic-impedance)。项目采用 [Apache License 2.0](https://github.com/WEIXUEP/microstrip-quasistatic-impedance/blob/main/LICENSE)。
