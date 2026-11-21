"""M0 占位入口 —— Codex 部在 main() 中实现 CLI（README 第 4/5 节为冻结契约）。

dsh 部只负责打包与入口注册（pyproject 的 [project.scripts] spdiff）。
本文件在 M1 之后归 Codex 部所有；M0 期间它存在的唯一意义是让
`spdiff --help` 在 pip install . 之后可执行，从而满足 M0 出口条件。

退出码（README 第 5 节，冻结）：0 无差异 / 1 有差异 / 2 uncertain / 3 输入错误。
"""

from __future__ import annotations

import argparse
import sys

from . import __version__

CORE_UNIMPLEMENTED = "spdiff 0.1.0: core not implemented yet (M1, Codex)"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="spdiff",
        description="Structural change report between two SPICE netlists.",
    )
    p.add_argument("before", nargs="?", help="baseline netlist (.sp/.cir/.net)")
    p.add_argument("after", nargs="?", help="revised netlist")
    p.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    p.add_argument("--format", choices=("md", "json"), default=None, help="output format")
    p.add_argument("-o", "--output", default=None, help="write report to file")
    p.add_argument("--version", action="version", version="spice-diff " + __version__)
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.before is None or args.after is None:
        parser.print_usage(sys.stderr)
        sys.stderr.write("spdiff: error: two netlists are required\n")
        return 3
    # M1 之前：任何真实调用一律按「输入错误」返回 3，绝不返回 0 冒充无差异。
    sys.stderr.write(CORE_UNIMPLEMENTED + "\n")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
