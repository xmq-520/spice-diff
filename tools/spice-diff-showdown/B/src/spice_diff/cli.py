"""spdiff CLI（Hermes 实现，供 ④ 对拍）：解析 → diff → Markdown/JSON。"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .core import (EXIT_INPUT_ERROR, diff, render_json, render_markdown)
from .parse import ParseError, parse_file


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
        return EXIT_INPUT_ERROR

    try:
        before = parse_file(args.before)
        after = parse_file(args.after)
    except ParseError as exc:
        # 解析失败：stdout 一个字都不出，绝不"尽力而为"出半截报告
        sys.stderr.write("%s\n" % exc)
        return EXIT_INPUT_ERROR

    result = diff(before, after)
    want_json = args.json or (args.format == "json")
    if want_json:
        text = render_json(result, args.before, args.after)
    else:
        text = render_markdown(result, args.before, args.after)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text if text.endswith("\n") else text + "\n")
        except OSError as exc:
            sys.stderr.write("spdiff: error: cannot write %s: %s\n" % (args.output, exc))
            return EXIT_INPUT_ERROR
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
