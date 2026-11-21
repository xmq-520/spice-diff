"""spice-diff — 两版 SPICE 网表的结构变更报告（Hermes 实现，④ 对拍用）。

模块：parse.py（解析） / core.py（归一化·对齐·diff·渲染） / cli.py（入口）。
退出码：0 无差异 / 1 有差异 / 2 uncertain / 3 输入错误。
"""

from __future__ import annotations

__version__ = "0.1.0"

EXIT_NO_DIFF = 0
EXIT_DIFF = 1
EXIT_UNCERTAIN = 2
EXIT_INPUT_ERROR = 3

__all__ = ["__version__", "EXIT_NO_DIFF", "EXIT_DIFF", "EXIT_UNCERTAIN", "EXIT_INPUT_ERROR"]
