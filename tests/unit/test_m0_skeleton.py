"""M0 冒烟测试（dsh 部）。

只测「骨架是否立得住」，不测 diff 语义 —— 语义测试归 Codex 的 tests/unit。
Codex 实现 M1 后可整目录保留本文件：它会在核心落地后自动变严
（test_core_placeholder_gone 一旦失败，说明入口已交接到位）。
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

# 干净克隆未 pip install . 时，从源码树直接可导入（dsh 部欠账，11-21 19:5x 补）。
_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if os.path.isdir(os.path.join(_SRC, "spice_diff")) and _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from spice_diff import (
    EXIT_DIFF,
    EXIT_INPUT_ERROR,
    EXIT_NO_DIFF,
    EXIT_UNCERTAIN,
    __version__,
)
from spice_diff.cli import build_parser, main


class TestPackage(unittest.TestCase):
    def test_version_is_semver(self):
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")

    def test_exit_codes_frozen_by_contract(self):
        # README 第 5 节：这四个值不许改。
        self.assertEqual((EXIT_NO_DIFF, EXIT_DIFF, EXIT_UNCERTAIN, EXIT_INPUT_ERROR), (0, 1, 2, 3))


class TestCliSurface(unittest.TestCase):
    def test_help_exits_zero(self):
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(SystemExit) as cm:
                build_parser().parse_args(["--help"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("usage: spdiff", out.getvalue())

    def test_positional_contract(self):
        a = build_parser().parse_args(["b.sp", "a.sp", "--json", "-o", "r.md"])
        self.assertEqual((a.before, a.after), ("b.sp", "a.sp"))
        self.assertTrue(a.json)
        self.assertEqual(a.output, "r.md")

    def test_format_choices_are_md_and_json_only(self):
        err = io.StringIO()
        with redirect_stderr(err):
            with self.assertRaises(SystemExit):
                build_parser().parse_args(["b", "a", "--format", "yaml"])

    def test_missing_operand_is_input_error(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = main([])
        self.assertEqual(rc, EXIT_INPUT_ERROR)


class TestPython39Syntax(unittest.TestCase):
    """PLAN.md 硬约束 3：禁 3.10+ 语法。这里做静态兜底。"""

    FORBIDDEN = [
        (re.compile(r"(?<![\w.'\"])\w+\s*\|\s*(None|str|int|float|bool|bytes)\b"), "PEP 604 X | None"),
        (re.compile(r":\s*list\["), "builtin generic list[...] annotation"),
        (re.compile(r":\s*dict\["), "builtin generic dict[...] annotation"),
        (re.compile(r":\s*tuple\["), "builtin generic tuple[...] annotation"),
        (re.compile(r"\bmatch\s+.+:\s*$"), "match statement"),
    ]

    def _sources(self):
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[2] / "src" / "spice_diff"
        return sorted(root.glob("*.py"))

    def test_sources_exist(self):
        self.assertTrue(self._sources(), "src/spice_diff has no .py files")

    def test_no_310_plus_syntax_in_src(self):
        offenders = []
        for path in self._sources():
            text = path.read_text(encoding="utf-8")
            if "from __future__ import annotations" not in text:
                offenders.append(path.name + ": missing __future__ annotations")
            for rx, label in self.FORBIDDEN:
                for m in rx.finditer(text):
                    line = text[: m.start()].count("\n") + 1
                    offenders.append("{}:{}: {}".format(path.name, line, label))
        self.assertEqual(offenders, [], "3.10+ syntax found:\n  " + "\n  ".join(offenders))


class TestJsonSchemaShape(unittest.TestCase):
    """README「JSON 结构（v0.1 固定，不许加字段）」——五个键，一个不多一个不少。"""

    REQUIRED = {"tool", "version", "summary", "changes", "exit_code"}
    SUMMARY_KEYS = {
        "device_added",
        "device_removed",
        "param_changed",
        "connection_changed",
        "model_changed",
        "uncertain",
    }

    def test_example_payload_validates(self):
        sample = json.dumps(
            {
                "tool": "spice-diff",
                "version": "0.1.0",
                "summary": {k: 0 for k in sorted(self.SUMMARY_KEYS)},
                "changes": [],
                "exit_code": 0,
            }
        )
        obj = json.loads(sample)
        self.assertEqual(set(obj), self.REQUIRED)
        self.assertEqual(set(obj["summary"]), self.SUMMARY_KEYS)


if __name__ == "__main__":
    unittest.main()
