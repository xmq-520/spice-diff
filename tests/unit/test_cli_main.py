"""CLI 入口 main() 的回归测试。

用真实临时网表跑真实入口：`--version`、缺参数、同文件自比、有差异、`-o` 落盘、
解析错误时 stdout 必须一个字节都不出。此前 tests/ 里没有任何一条调用 cli.main()。
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

# 本机 site-packages 里装着旧的 spice_diff 0.1.0；这里显式指向仓库源码，
# 免得单跑这一条测试时静默测到旧包（其它测试文件用的是同一写法）。
_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "src"))
if os.path.isdir(os.path.join(_SRC, "spice_diff")) and _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from spice_diff import __version__
from spice_diff.cli import main
from spice_diff.core import (
    EXIT_DIFF,
    EXIT_INPUT_ERROR,
    EXIT_NO_DIFF,
    EXIT_UNCERTAIN,
)

BEFORE = "title\nV1 in 0 1\nR1 in 0 1k\nC1 in 0 1p\n.end\n"
# 只改参数：身份确定 → 退出码 1
AFTER = "title\nV1 in 0 1\nR1 in 0 2k\nC1 in 0 1p\n.end\n"
# 多一个同类器件：数量可定、身份不可定 → 退出码 2（不猜）
AFTER_ADDED = "title\nV1 in 0 1\nR1 in 0 1k\nC1 in 0 1p\nC2 in 0 1p\n.end\n"


class CliMainTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.before = self._write("before.sp", BEFORE)
        self.after = self._write("after.sp", AFTER)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return path

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_version_prints_package_version_and_exits_zero(self):
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as caught:
            main(["--version"])
        self.assertEqual(0, caught.exception.code)
        self.assertIn(__version__, out.getvalue())

    def test_missing_netlists_is_input_error_not_traceback(self):
        rc, out, err = self._run([self.before])
        self.assertEqual(EXIT_INPUT_ERROR, rc)
        self.assertEqual("", out, "报用法错误时 stdout 不许有内容")
        self.assertIn("two netlists are required", err)

    def test_same_file_against_itself_exits_zero(self):
        rc, out, err = self._run([self.before, self.before])
        self.assertEqual(EXIT_NO_DIFF, rc)
        self.assertEqual("", err)
        self.assertTrue(out.strip(), "自比也要出报告，不能空")

    def test_structural_difference_exits_one(self):
        rc, out, err = self._run([self.before, self.after])
        self.assertEqual(EXIT_DIFF, rc)
        self.assertEqual("", err)
        self.assertIn("R1", out)
        self.assertIn("2k", out)

    def test_ambiguous_addition_exits_two_not_one(self):
        added = self._write("added.sp", AFTER_ADDED)
        rc, out, err = self._run([self.before, added])
        self.assertEqual(EXIT_UNCERTAIN, rc, "数量可定、身份不可定时必须退 2，不许猜成 1")
        self.assertIn("不确定", out)

    def test_json_flag_emits_parsable_json_with_exit_code(self):
        rc, out, err = self._run([self.before, self.after, "--json"])
        self.assertEqual(EXIT_DIFF, rc)
        payload = json.loads(out)
        self.assertEqual(EXIT_DIFF, payload["exit_code"])

    def test_output_file_keeps_stdout_empty(self):
        target = os.path.join(self.dir, "report.md")
        rc, out, err = self._run([self.before, self.after, "-o", target])
        self.assertEqual(EXIT_DIFF, rc)
        self.assertEqual("", out, "-o 时报告只进文件，不重复打到 stdout")
        with open(target, encoding="utf-8") as fh:
            self.assertIn("R1", fh.read())

    def test_parse_error_writes_nothing_to_stdout(self):
        broken = self._write("broken.sp", "title\n.ends\n")
        rc, out, err = self._run([self.before, broken])
        self.assertEqual(EXIT_INPUT_ERROR, rc)
        self.assertEqual("", out, "解析失败绝不出半截报告")
        self.assertIn(".ends", err)


if __name__ == "__main__":
    unittest.main()
