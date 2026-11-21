"""边界用例：真实网表里常见、样例集里没有的写法。

每条都必须碰到网表并断言退出码，不做纯函数自证。
`.param` 那条按契约第 6 条固化：v0.1 已知假阴性，用 expectedFailure 钉着，
等 v0.2 修好后它会变成 unexpected success，那时才翻绿——不许为了绿灯删证据。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_src():
    """向上找含 src/spice_diff 的目录。

    本文件可能落在两处：对拍版 `B/tests/`（src 在上层）、仓库 `tests/blackbox/`
    （src 在仓库根）。写死一层 dirname 挪个位置就静默失效，所以往上走。
    """
    cand = os.environ.get("SPDIFF_SRC")
    if cand and os.path.isdir(os.path.join(cand, "spice_diff")):
        return os.path.abspath(cand)
    d = HERE
    for _ in range(6):
        if os.path.isdir(os.path.join(d, "src", "spice_diff")):
            return os.path.abspath(os.path.join(d, "src"))
        d = os.path.dirname(d)
        if d in ("", os.path.sep):
            break
    return None


SRC = _find_src()


def run(*args):
    if SRC is None:      # 不许静默全绿：找不到实现就当场炸
        raise AssertionError("找不到 src/spice_diff，测试无法真跑；拒绝伪通过")
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run([sys.executable, "-m", "spice_diff.cli"] + [str(a) for a in args],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)
    return proc.returncode, proc.stdout, proc.stderr


def pair(before: str, after: str):
    d = tempfile.mkdtemp()
    p1, p2 = os.path.join(d, "b.sp"), os.path.join(d, "a.sp")
    with open(p1, "wb") as f:
        f.write(before.encode("utf-8"))
    with open(p2, "wb") as f:
        f.write(after.encode("utf-8"))
    return p1, p2


class TestNetlistForms(unittest.TestCase):
    def test_crlf_line_endings(self):
        b = "V1 in 0 DC 1\r\nR1 in n1 1k\r\nR2 n1 0 2k\r\n.end\r\n"
        a = "V1 in 0 DC 1\r\nR1 in n1 1k\r\nR2 n1 0 3k\r\n.end\r\n"
        rc, out, err = run(*pair(b, a))
        self.assertEqual(rc, 1, err)
        self.assertIn("R2 | 2k (2e3) | 3k (3e3)", out)
        self.assertNotIn("R1 |", out)

    def test_tabs_and_inline_comment(self):
        b = "V1\tin\t0\tDC\t1\nR1\tin\tn1\t1k\t; load\nR2\tn1\t0\t2k\n.end\n"
        a = "V1\tin\t0\tDC\t1\nR1\tin\tn1\t1k\t; load\nR2\tn1\t0\t3k\n.end\n"
        rc, out, err = run(*pair(b, a))
        self.assertEqual(rc, 1, err)
        self.assertIn("R2 | 2k (2e3) | 3k (3e3)", out)

    def test_bom_prefixed_file(self):
        b = "\ufeffV1 in 0 DC 1\nR1 in n1 1k\n.end\n"
        a = "\ufeffV1 in 0 DC 1\nR1 in n1 2k\n.end\n"
        rc, out, err = run(*pair(b, a))
        self.assertEqual(rc, 1, err)
        self.assertIn("R1 | 1k (1e3) | 2k (2e3)", out)


class TestTopology(unittest.TestCase):
    def test_subckt_port_swap_is_connection_change(self):
        b = ("X1 in out mid amp\n.subckt amp a b c\nR1 a b 1k\nR2 b c 2k\n.ends\n.end\n")
        a = ("X1 in out mid amp\n.subckt amp a b c\nR1 b a 1k\nR2 b c 2k\n.ends\n.end\n")
        rc, out, err = run(*pair(b, a))
        self.assertEqual(rc, 1, err)
        self.assertIn("connection_changed | `amp` | R1", out)

    def test_ground_swap_is_connection_change(self):
        b = "V1 in 0 DC 1\nR1 in n1 1k\nR2 n1 0 2k\n.end\n"
        a = "V1 in 0 DC 1\nR1 out n1 1k\nR2 n1 0 2k\n.end\n"
        rc, out, err = run(*pair(b, a))
        self.assertEqual(rc, 1, err)

    def test_global_net_rename_is_visible(self):
        b = ".global vdd\nV1 vdd 0 DC 1\nR1 vdd n1 1k\n.end\n"
        a = ".global vdd\nV1 vdd 0 DC 1\nR1 vcc n1 1k\n.end\n"
        rc, out, err = run(*pair(b, a))
        self.assertEqual(rc, 1, "vdd 是锚点，改成 vcc 必须是差异；stderr=%s" % err)


class TestParamKnownGap(unittest.TestCase):
    """契约第 6 条：v0.1 不解析 .param，值变了会漏报。"""

    def test_param_used_but_unchanged_still_diffs_others(self):
        b = "V1 in 0 DC 1\n.param rr=1k\nR1 in n1 rr\nR2 n1 0 2k\n.end\n"
        a = "V1 in 0 DC 1\n.param rr=1k\nR1 in n1 rr\nR2 n1 0 3k\n.end\n"
        rc, out, err = run(*pair(b, a))
        self.assertEqual(rc, 1, err)
        self.assertIn("R2 | 2k (2e3) | 3k (3e3)", out)
        self.assertNotIn("R1 |", out, "参数名未变，R1 不该报差异")

    @unittest.expectedFailure
    def test_param_value_change_is_missed_in_v01(self):
        b = "V1 in 0 DC 1\n.param rr=1k\nR1 in n1 rr\nR2 n1 0 2k\n.end\n"
        a = "V1 in 0 DC 1\n.param rr=2k\nR1 in n1 rr\nR2 n1 0 2k\n.end\n"
        rc, out, err = run(*pair(b, a))
        # v0.2 修好后这里会 unexpected success，届时把本装饰器删掉
        self.assertNotEqual(rc, 0, "只改 .param 值却报等价，就是假阴性：\n" + out)
class TestIncludeKnownGap(unittest.TestCase):
    """契约第 6 条：v0.1 不展开 .include，被包含文件的内容不参与比对。"""

    NET_B = b"V1 in 0 DC 1\n.include sub1.sp\nR2 n1 0 2k\n.end\n"
    NET_A_SAME_INC = b"V1 in 0 DC 1\n.include sub1.sp\nR2 n1 0 3k\n.end\n"
    NET_A_OTHER_INC = b"V1 in 0 DC 1\n.include sub2.sp\nR2 n1 0 2k\n.end\n"

    def _write(self, d, name, body):
        path = os.path.join(d, name)
        with open(path, "wb") as f:
            f.write(body)
        return path

    def test_include_line_is_ignored_but_rest_still_diffs(self):
        d = tempfile.mkdtemp()
        b = self._write(d, "b.sp", self.NET_B)
        a = self._write(d, "a.sp", self.NET_A_SAME_INC)
        rc, out, err = run(b, a)
        self.assertEqual(rc, 1, err)
        self.assertIn("R2 | 2k (2e3) | 3k (3e3)", out)

    @unittest.expectedFailure
    def test_include_target_change_is_missed_in_v01(self):
        d = tempfile.mkdtemp()
        self._write(d, "sub1.sp", b"R1 in n1 1k\n")
        self._write(d, "sub2.sp", b"R1 in n1 2k\n")
        b = self._write(d, "b.sp", self.NET_B)
        a = self._write(d, "a.sp", self.NET_A_OTHER_INC)
        rc, out, err = run(b, a)
        # v0.2 展开 include 后这里会 unexpected success，届时删掉装饰器
        self.assertNotEqual(rc, 0, "include 指向不同文件却报等价，就是假阴性：\n" + out)


if __name__ == "__main__":
    unittest.main()
