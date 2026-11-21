"""spice-diff — structural change report between two SPICE netlists.

v0.1 契约见 README.md。本包只暴露版本号与退出码常量；
解析 / 归一化 / 对齐 / diff 核心由 Codex 部在 parser.py、normalize.py、
align.py、diff.py 中实现，CLI 入口为 cli.py::main。
"""

from __future__ import annotations

__version__ = "0.1.0"

# 退出码（README 第 5 节，冻结）
EXIT_NO_DIFF = 0
EXIT_DIFF = 1
EXIT_UNCERTAIN = 2
EXIT_INPUT_ERROR = 3

__all__ = [
    "__version__",
    "EXIT_NO_DIFF",
    "EXIT_DIFF",
    "EXIT_UNCERTAIN",
    "EXIT_INPUT_ERROR",
]
