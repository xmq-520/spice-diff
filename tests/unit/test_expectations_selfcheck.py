"""黄金期望自检（dsh 部，与 OpenCode 的 tests/golden 不重叠）。

这里**不跑 spdiff**，只校验 Hermes 写的 `examples/expected_*.md` 与
契约 README 是否自洽 —— 因为「黄金期望本身写错」会让 M2 出现
「实现没错、绿灯变红灯」的假失败（OpenCode 15:12 已点出这一风险）。

期望目录默认取共享目录（本机可读、对 dsh 只读），可用
SPICE_DIFF_SHARED 或 --shared 覆盖。
"""

from __future__ import annotations

import os
import re
import unittest

DEFAULT_SHARED = r"C:\Users\hp\Documents\ClawChat\shared\spice-diff"

KINDS = {
    "device_added",
    "device_removed",
    "param_changed",
    "connection_changed",
    "model_changed",
    "uncertain",
}


def shared_root():
    return os.environ.get("SPICE_DIFF_SHARED", DEFAULT_SHARED)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class TestExpectedFilesSelfConsistent(unittest.TestCase):
    """expected_*.md 只能使用契约允许的六类差异名。"""

    def expected_files(self):
        d = os.path.join(shared_root(), "examples")
        if not os.path.isdir(d):
            return []
        return sorted(f for f in os.listdir(d) if f.startswith("expected_") and f.endswith(".md"))

    def test_expected_files_present(self):
        files = self.expected_files()
        self.assertTrue(files, "examples/expected_*.md not found under " + shared_root())

    def test_only_contract_kind_names_used(self):
        bad = []
        for name in self.expected_files():
            text = read(os.path.join(shared_root(), "examples", name))
            for tok in re.findall(r"\b[a-z][a-z_]*_(?:changed|added|removed)\b|\buncertain\b", text):
                if tok not in KINDS:
                    bad.append("{}: {}".format(name, tok))
        self.assertEqual(bad, [], "non-contract diff kind names in expected files: " + "; ".join(bad))

    def test_every_pair_has_a_pair(self):
        d = os.path.join(shared_root(), "examples")
        if not os.path.isdir(d):
            self.skipTest("no examples dir")
        names = set(os.listdir(d))
        pairs = sorted({f.split("_")[1] for f in names if re.match(r"pair_([a-z])_before\.sp$", f)})
        self.assertTrue(pairs, "no pair_*_before.sp")
        for p in pairs:
            self.assertIn("pair_{}_after.sp".format(p), names, "pair_{} has no after".format(p))


class TestNetlistSyntaxSanity(unittest.TestCase):
    """输入网表须是契约第 1 节支持的器件/指令，否则 M2 的失败会误判为实现问题。"""

    DEVICE_LEADERS = set("RCLDMQXVI")
    DIRECTIVES = {
        ".subckt",
        ".ends",
        ".model",
        ".param",
        ".global",
        ".include",
        ".end",
        ".title",
    }

    def netlist_files(self):
        d = os.path.join(shared_root(), "examples")
        if not os.path.isdir(d):
            return []
        return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".sp"))

    def test_netlists_exist(self):
        self.assertTrue(self.netlist_files(), "no .sp examples under shared/examples")

    def test_statements_use_supported_vocab(self):
        offenders = []
        for path in self.netlist_files():
            for lineno, raw in enumerate(read(path).splitlines(), 1):
                line = raw.strip()
                if not line or line.startswith("*"):
                    continue
                head = line.split()[0]
                if head.startswith("."):
                    if head.lower() not in self.DIRECTIVES:
                        offenders.append("{}:{}: unsupported directive {}".format(os.path.basename(path), lineno, head))
                elif line.startswith("+"):
                    continue
                elif head[0].upper() not in self.DEVICE_LEADERS:
                    offenders.append("{}:{}: unsupported statement leader {}".format(os.path.basename(path), lineno, head))
        self.assertEqual(offenders, [], "unsupported syntax in examples:\n  " + "\n  ".join(offenders))


class TestContractNumbers(unittest.TestCase):
    """契约第 2 节数值归一化的最小断言集（给 Codex 当靶，也验证契约自洽）。"""

    SUFFIX = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6, "g": 1e9, "t": 1e12}

    def parse(self, token):
        t = token.strip().lower()
        m = re.match(r"^([+-]?[0-9.]+(?:e[+-]?\d+)?)([a-zµ]*)$", t)
        self.assertIsNotNone(m, "unparsable value " + token)
        num, unit = float(m.group(1)), m.group(2)
        if unit in ("", "ohm", "v", "a", "f", "p", "n", "u", "m", "k", "meg", "g", "t"):
            if unit == "m":
                return num * 1e-3  # 契约：1m 一律为毫，不为兆
            if unit == "meg":
                return num * 1e6
            if unit in ("", "ohm", "v", "a"):
                return num
            return num * self.SUFFIX[unit]
        raise AssertionError("unknown unit " + unit)

    def test_contract_examples_agree(self):
        for a, b in [("1k", "1K"), ("1k", "1000"), ("1k", "1e3"), ("1MEG", "1meg"), ("1MEG", "1e6")]:
            self.assertAlmostEqual(self.parse(a), self.parse(b), places=12, msg="{} vs {}".format(a, b))

    def test_m_is_milli_not_mega(self):
        self.assertAlmostEqual(self.parse("1m"), 1e-3)
        self.assertGreater(self.parse("1MEG"), self.parse("1m"))


if __name__ == "__main__":
    unittest.main()
