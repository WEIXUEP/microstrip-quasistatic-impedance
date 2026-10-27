# 常见问题

## 找不到 gmsh / skfem / scipy 模块

通常是安装依赖的 Python 与运行脚本的 Python 不同。用同一个解释器安装和运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe microstrip_quasistatic.py
```

在 Linux/macOS 中将解释器路径换成 `.venv/bin/python`。包名为 `scikit-fem`，导入名为 `skfem`。

## Linux 缺少 libGLU.so.1

Gmsh Python 包需要本机动态库，即使脚本没有打开 GUI，也可能在导入时加载这些库。Ubuntu/Debian 通常可以安装：

```bash
sudo apt-get update
sudo apt-get install libglu1-mesa
```

其他发行版请按实际错误查找对应系统包。若提示缺少 `venv`，Ubuntu/Debian 通常需要 `python3-venv`。

## Windows 提示 DLL load failed

确认 Python 架构与安装的包匹配，并使用 `python -m pip install --upgrade gmsh` 获取适配当前环境的 wheel。继续失败时保存完整错误、Python 版本和系统架构，检查是否缺少该 wheel 所需的本机运行库。

## trace_thickness must be smaller than h2

T 必须小于 H2，因为信号线从两层介质界面向上延伸，H2 包含 T。其他输入约束见[几何说明](geometry.md)。

## failed to identify signal or ground boundary / DOFs

先检查长度是否为正、走线是否在基板内、T 是否小于 H2，以及有没有把 mm 当成 mil。极小尺度还可能接近几何识别使用的绝对容差；这种情况需要检查源码容差，不能仅靠加密网格解决。

## 结果和 Polar 或其他工具不同

先对齐 W1/W2 梯形方向、H2 是否包含铜厚、材料、有限宽地和空气盒边界。然后分别做网格与计算域收敛。历史表只代表所列案例，详细限制见[对照案例](validation.md)。

## 改了 --order 2，但 .msh 仍然是一阶网格

这是当前实现的正常行为。P2 电位空间由 scikit-fem 构造，导出的 Gmsh 网格仍是一阶，见[阶数说明](cli.md)。

## 网格很多、内存占用大或求解慢

面积因子越大，网格越细。先用默认值或较粗网格确认几何，再逐级加密。P2 通常比 P1 使用更多自由度；不要同时大幅增加所有网格因子和空气盒尺寸。

## 为什么没有电场图、S 参数或频率选项？

目前只导出网格和准静态标量结果。电位存在求解返回值中，尚未实现场文件输出；S 参数、损耗和三维全波分析超出当前程序范围。

## 文档本地构建失败

在项目根目录执行 `python -m pip install -r requirements-docs.txt`，再运行 `python -m mkdocs build --strict`。严格构建中的内部链接或配置警告也会导致失败，需按日志修正。

## GitHub Pages 返回 404

在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。检查 **Actions → Documentation** 工作流是否完成 build 和 deploy；仅 build 成功还没有发布。项目网址包含仓库名路径，完整地址见[发布步骤](development.md#github-pages)。

## 如何报告问题

在 [GitHub Issues](https://github.com/WEIXUEP/microstrip-quasistatic-impedance/issues) 提供：完整运行命令、预期与实际现象、错误日志、`result.json`（如已生成）、操作系统、Python/依赖版本和 Git 提交号。外部工具对比请附模型与边界定义。
