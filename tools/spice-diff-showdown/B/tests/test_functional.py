"""功能测试：真跑 spdiff，真断言退出码与输出。

存在的意义就是把「16 tests OK 但 core 零字节」这种绿灯假象钉死：
每条测试都必须碰到 examples/ 里的网表，且断言的是 rc 与输出内容。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
EX = os.environ.get("SPDIFF_EXAMPLES") or os.path.join(
    os.path.dirname(ROOT), "..", "shared", "spice-diff", "examples")
EX = os.path.abspath(EX)


def run(*args):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run([sys.executable, "-m", "spice_diff.cli"] + list(args),
                          capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def pairs(p):
    return (os.path.join(EX, "pair_%s_before.sp" % p),
            os.path.join(EX, "pair_%s_after.sp" % p))


class TestExamples(unittest.TestCase):
    def test_pair_a_is_zero_diff(self):
        rc, out, err = run(*pairs("a"))
        self.assertEqual(rc, 0, err)
        self.assertIn("无结构差异", out)
        self.assertNotIn("| param_changed", out)

    def test_pair_b_four_changes(self):
        rc, out, err = run(*pairs("b"))
        self.assertEqual(rc, 1, err)
        self.assertIn("器件新增：1", out)
        self.assertIn("器件删除：1", out)
        self.assertIn("参数变化：1", out)
        self.assertIn("模型变化：1", out)
        self.assertIn("| param_changed | 顶层 | R2 | 2k (2e3) | 3k (3e3) |", out)
        self.assertIn("| device_removed | 顶层 | C1 | C1 n1 0 10p | — |", out)
        self.assertIn("| device_added | 顶层 | D2 | — | D2 0 out DMOD |", out)
        self.assertIn("model_changed | 顶层 | DMOD | D(IS=1e-14 N=1) | D(IS=1e-14 N=1.05)", out)

    def test_pair_c_reports_inside_subckt(self):
        rc, out, err = run(*pairs("c"))
        self.assertEqual(rc, 1, err)
        self.assertIn("param_changed | `buf` | R1 | 1k (1e3) | 2k (2e3)", out)
        self.assertNotIn("顶层 | R1", out)

    def test_pair_d_is_uncertain_not_guessed(self):
        rc, out, err = run(*pairs("d"), "--json")
        self.assertEqual(rc, 2, err)
        doc = json.loads(out)
        self.assertEqual(doc["summary"]["uncertain"], 1)
        self.assertEqual(doc["exit_code"], 2)
        ch = doc["changes"][0]
        self.assertEqual(ch["kind"], "device_removed")
        self.assertIsNone(ch["refdes"], "身份不可定时不许猜 refdes")
        self.assertEqual(ch["candidates"], ["R1", "R2"])

    def test_bad_syntax_exits_3_with_line_and_no_stdout(self):
        rc, out, err = run(os.path.join(EX, "error_bad_syntax.sp"), pairs("a")[0])
        self.assertEqual(rc, 3)
        self.assertEqual(out, "", "解析失败时 stdout 必须为空")
        self.assertIn("error_bad_syntax.sp:", err)
        self.assertIn("M1", err)

    def test_missing_file_exits_3(self):
        rc, out, err = run(os.path.join(EX, "no_such_file.sp"), pairs("a")[0])
        self.assertEqual(rc, 3)
        self.assertIn("文件不存在", err)


class TestContract(unittest.TestCase):
    def test_deterministic_bytes(self):
        a = run(*pairs("b"))[1]
        b = run(*pairs("b"))[1]
        self.assertEqual(a, b, "同一对输入必须字节级一致")

    def test_json_schema_frozen(self):
        rc, out, err = run(*pairs("b"), "--json")
        doc = json.loads(out)
        self.assertEqual(list(doc.keys()),
                         ["tool", "version", "summary", "changes", "exit_code"])
        self.assertEqual(list(doc["summary"].keys()),
                         ["device_added", "device_removed", "param_changed",
                          "connection_changed", "model_changed", "uncertain"])
        keys = [(c["scope"], c["refdes"] or "", c["kind"]) for c in doc["changes"]]
        self.assertEqual(keys, sorted(keys), "changes 必须按 (scope, refdes, kind) 升序")

    def test_no_absolute_paths_in_report(self):
        rc, out, err = run(*pairs("b"))
        self.assertNotIn(EX, out)
        self.assertNotIn("C:", out)

    def test_version(self):
        rc, out, err = run("--version")
        self.assertEqual(rc, 0)
        self.assertIn("spice-diff 0.1.0", out)


if __name__ == "__main__":
    unittest.main()
