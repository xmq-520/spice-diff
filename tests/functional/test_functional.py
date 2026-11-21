"""功能测试：真跑 spdiff，真断言退出码与输出。

存在的意义就是把「16 tests OK 但 core 零字节」这种绿灯假象钉死：
每条测试都必须碰到网表，断言的是 rc 与输出内容。
回归集 x1–x3 覆盖对拍里暴露过的真实缺陷（RKM 写法、同签名身份、.global 锚点）。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# 两种布局都要能跑：
#   对拍原样  tests/ + src/ 同级      -> ROOT = 版本根
#   落进仓库  tests/functional/       -> ROOT = 仓库根（src/、examples/ 在那儿）
ROOT = HERE if os.path.isdir(os.path.join(os.path.dirname(HERE), "src"))     else os.path.dirname(os.path.dirname(HERE))
SRC = os.environ.get("SPDIFF_SRC") or os.path.join(ROOT, "src")


def _find(*cands):
    for c in cands:
        if c and os.path.isdir(c):
            return os.path.abspath(c)
    return None


EX = _find(
    os.environ.get("SPDIFF_EXAMPLES"),
    os.path.join(ROOT, "examples"),
    os.path.join(os.path.dirname(ROOT), "..", "shared", "spice-diff", "examples"),
)
EXTRA = _find(
    os.environ.get("SPDIFF_EXTRAS"),
    os.path.join(HERE, "extras"),                  # 落仓库：tests/functional/extras
    os.path.join(ROOT, "extras"),                  # 对拍原样：版本根 extras
    os.path.join(os.path.dirname(ROOT), "extras"),
)


def run(*args):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONUTF8"] = "1"           # 不靠外部 locale，CI 上也一样
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, "-m", "spice_diff.cli"] + [str(a) for a in args],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)
    return proc.returncode, proc.stdout, proc.stderr


def ex(p):
    return (os.path.join(EX, "pair_%s_before.sp" % p),
            os.path.join(EX, "pair_%s_after.sp" % p))


def xt(p):
    return (os.path.join(EXTRA, "%s_before.sp" % p),
            os.path.join(EXTRA, "%s_after.sp" % p))


class TestExamples(unittest.TestCase):
    def test_pair_a_is_zero_diff(self):
        rc, out, err = run(*ex("a"))
        self.assertEqual(rc, 0, err)
        self.assertIn("无结构差异", out)
        self.assertNotIn("| param_changed", out)

    def test_pair_b_four_changes(self):
        rc, out, err = run(*ex("b"))
        self.assertEqual(rc, 1, err)
        for s in ("器件新增：1", "器件删除：1", "参数变化：1", "模型变化：1"):
            self.assertIn(s, out)
        self.assertIn("| param_changed | 顶层 | R2 | 2k (2e3) | 3k (3e3) |", out)
        self.assertIn("| device_removed | 顶层 | C1 | C1 n1 0 10p | — |", out)
        self.assertIn("| device_added | 顶层 | D2 | — | D2 0 out DMOD |", out)
        self.assertIn("model_changed | 顶层 | DMOD | D(IS=1e-14 N=1) | D(IS=1e-14 N=1.05)", out)

    def test_pair_c_reports_inside_subckt(self):
        rc, out, err = run(*ex("c"))
        self.assertEqual(rc, 1, err)
        self.assertIn("param_changed | `buf` | R1 | 1k (1e3) | 2k (2e3)", out)
        self.assertNotIn("顶层 | R1", out)

    def test_pair_d_is_uncertain_not_guessed(self):
        rc, out, err = run(*(ex("d") + ("--json",)))
        self.assertEqual(rc, 2, err)
        doc = json.loads(out)
        self.assertEqual(doc["summary"]["uncertain"], 1)
        self.assertEqual(doc["exit_code"], 2)
        ch = doc["changes"][0]
        self.assertEqual(ch["kind"], "device_removed")
        self.assertIsNone(ch["refdes"], "身份不可定时不许猜 refdes")
        self.assertEqual(ch["candidates"], ["R1", "R2"])

    def test_bad_syntax_exits_3_with_line_and_no_stdout(self):
        rc, out, err = run(os.path.join(EX, "error_bad_syntax.sp"), ex("a")[0])
        self.assertEqual(rc, 3)
        self.assertEqual(out, "", "解析失败时 stdout 必须为空")
        self.assertIn("error_bad_syntax.sp:", err)
        self.assertIn("M1", err)

    def test_missing_file_exits_3(self):
        rc, out, err = run(os.path.join(EX, "no_such_file.sp"), ex("a")[0])
        self.assertEqual(rc, 3)
        self.assertIn("文件不存在", err)


class TestNumbers(unittest.TestCase):
    """RKM 写法：4k7 = 4.7e3 = 4700。x1 就是栽在这上面。"""

    def _cmp(self, b, a):
        d = tempfile.mkdtemp()
        p1, p2 = os.path.join(d, "b.sp"), os.path.join(d, "a.sp")
        with open(p1, "w", encoding="utf-8") as f:
            f.write(b)
        with open(p2, "w", encoding="utf-8") as f:
            f.write(a)
        return run(p1, p2)

    def test_rkm_equivalent(self):
        for b, a in (("4k7", "4.7e3"), ("4k7", "4700"), ("1R5", "1.5"), ("2M2", "2.2e-3")):
            rc, out, err = self._cmp("V1 in 0 DC 1\nR1 in n1 %s\n.end\n" % b,
                                     "V1 in 0 DC 1\nR1 in n1 %s\n.end\n" % a)
            self.assertEqual(rc, 0, "%s 与 %s 必须判等价，实得 rc=%d\n%s" % (b, a, rc, out))

    def test_rkm_real_change_detected(self):
        rc, out, err = self._cmp("V1 in 0 DC 1\nR1 in n1 4k7\n.end\n",
                                 "V1 in 0 DC 1\nR1 in n1 5k1\n.end\n")
        self.assertEqual(rc, 1, out)
        self.assertIn("4k7 (4.7e3)", out)
        self.assertIn("5k1 (5.1e3)", out)


@unittest.skipIf(EXTRA is None, "extras 目录不在")
class TestExtras(unittest.TestCase):
    """对拍加赛用过的三对，固化为回归断言。"""

    def test_x1_subckt_change_and_rkm(self):
        rc, out, err = run(*xt("x1"))
        self.assertEqual(rc, 1, err)
        self.assertIn("param_changed | `lvl` | R9", out)      # 子电路内改动，不展平
        self.assertIn("param_changed | 顶层 | R2 | 10k (1e4) | 22k (2.2e4)", out)
        self.assertIn("device_added | 顶层 | C2", out)
        self.assertNotIn("| R1 |", out, "4k7 与 4.7e3 等价，不许报 R1")

    def test_x2_same_signature_is_uncertain(self):
        rc, out, err = run(*(xt("x2") + ("--json",)))
        self.assertEqual(rc, 2, err)
        ch = json.loads(out)["changes"][0]
        self.assertEqual(ch["kind"], "device_removed")
        self.assertIsNone(ch["refdes"])
        # R1 在 in/n1 上，拓扑可区分；只有 R2/R3 不可分
        self.assertEqual(ch["candidates"], ["R2", "R3"])

    def test_x3_global_anchor(self):
        rc, out, err = run(*xt("x3"))
        self.assertEqual(rc, 1, err)
        self.assertIn("param_changed | 顶层 | R2 | 1k (1e3) | 2k (2e3)", out)
        self.assertIn("device_added | 顶层 | R4", out)


class TestContract(unittest.TestCase):
    def test_deterministic_bytes(self):
        self.assertEqual(run(*ex("b"))[1], run(*ex("b"))[1],
                         "同一对输入必须字节级一致")

    def test_json_schema_frozen(self):
        doc = json.loads(run(*(ex("b") + ("--json",)))[1])
        self.assertEqual(list(doc.keys()),
                         ["tool", "version", "summary", "changes", "exit_code"])
        self.assertEqual(list(doc["summary"].keys()),
                         ["device_added", "device_removed", "param_changed",
                          "connection_changed", "model_changed", "uncertain"])
        keys = [(c["scope"], c["refdes"] or "", c["kind"]) for c in doc["changes"]]
        self.assertEqual(keys, sorted(keys), "changes 必须按 (scope, refdes, kind) 升序")

    def test_no_absolute_paths_in_report(self):
        out = run(*ex("b"))[1]
        self.assertNotIn(EX, out)
        self.assertNotIn("C:", out)

    def test_version(self):
        rc, out, err = run("--version")
        self.assertEqual(rc, 0)
        self.assertRegex(out.strip(), r'^spice-diff \d+\.\d+\.\d+$')


if __name__ == "__main__":
    unittest.main()
