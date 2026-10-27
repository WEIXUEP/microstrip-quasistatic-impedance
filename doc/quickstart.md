# 安装与快速开始

## 环境要求

- Python **3.10+**；文档发布工作流使用 Python 3.11。
- 可安装 Python 包的网络环境。
- Gmsh Python 包所需的本机动态库；无需单独安装 Gmsh 桌面程序。

运行依赖见 `requirements.txt`：Gmsh、NumPy、SciPy 和 scikit-fem。文档依赖独立放在 `requirements-docs.txt`，只运行计算时不需要安装。

## 克隆仓库

```shell
git clone https://github.com/WEIXUEP/microstrip-quasistatic-impedance.git
cd microstrip-quasistatic-impedance
```

## Windows PowerShell

以下写法直接调用虚拟环境中的 Python，无需修改 PowerShell 执行策略或激活脚本：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe microstrip_quasistatic.py
```

查看参数帮助：

```powershell
.\.venv\Scripts\python.exe microstrip_quasistatic.py --help
```

## Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python microstrip_quasistatic.py
```

在部分 Ubuntu/Debian 最小化环境中，可能需要 `python3-venv` 和 `libglu1-mesa` 系统包。具体动态库报错见[常见问题](troubleshooting.md)。

## 自定义一个梯形走线 {#custom-case}

以下例子使用 H1=5、H2=5、W1=20、W2=50、T=1 mil，二阶有限元。命令放在一行，可在 PowerShell 和 Bash 中使用。运行前将 `python` 换成上面对应的虚拟环境 Python 路径，或激活虚拟环境。

```shell
python microstrip_quasistatic.py --h1 5 --h2 5 --er1 3.66 --er2 4.2 --w1 20 --w2 50 --trace-thickness 1 --order 2 --output output/custom
```

本例 W2 > W1，表示上宽下窄的梯形；矩形走线需要显式设置 `--w1` 和 `--w2` 为相同数值。

## 检查结果

程序输出网格顶点数、三角形数、有限元自由度数、电容、相速度、电感和阻抗。默认文件为：

```text
output/
├── microstrip.msh
└── result.json
```

读取关键字段：

```python
import json
from pathlib import Path

result = json.loads(Path("output/result.json").read_text(encoding="utf-8"))
print(f"Z0 = {result['characteristic_impedance_ohm']:.6f} Ω")
print(f"εeff = {result['effective_permittivity']:.6f}")
```

`--output` 指定相对路径时，相对于命令执行目录；省略该参数时，输出固定在脚本所在目录的 `output/`。同一输出目录再次运行会覆盖原文件，参数扫描应使用不同目录。

下一步：[核对几何与边界](geometry.md)、[查看完整参数](cli.md)、[验证结果收敛](validation.md)。
