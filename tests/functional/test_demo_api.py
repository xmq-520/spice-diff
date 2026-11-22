"""公开 API 组合用法测试（原 tools/demo.py 的落点）。

为什么要这条：v0.1.3 之前 `tests/` 里没有任何一条调用 `parse_text` /
`render_markdown`，也就是说「三个公开接口能组合出一份报告」这件事没人守。
这条测试每次 `unittest discover` 都会自动验一遍，不依赖任何人记得手动跑示例。

它同时是给读者照抄的写法样板：解析 → 比对 → 出报告，三步，只用公开接口。
口径必须与 README 一致，改 README 的用法说明时记得同步这里。
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# 两种布局都要能跑（与 test_functional.py 同法）：
#   落进仓库  tests/functional/  -> ROOT = 仓库根（src/ 在那儿）
#   对拍原样  tests/ + src/ 同级 -> ROOT = 版本根
ROOT = HERE if os.path.isdir(os.path.join(os.path.dirname(HERE), "src")) \
    else os.path.dirname(os.path.dirname(HERE))
SRC = os.environ.get("SPDIFF_SRC") or os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from spice_diff.core import diff, render_markdown      # noqa: E402  2. 比对  3. 出报告
from spice_diff.parse import parse_text                # noqa: E402  1. 解析

# LDO 反馈网络改版：反馈电阻 100k → 120k，另加一颗前馈电容 Cc。
# 注意单位写法：想写 2.2MΩ 必须写 2.2MEG 或 2.2e6，写 2M2 会被读成 0.0022Ω。
BEFORE = """* LDO 反馈网络 v1
Vin in 0 DC 1.2
Rf out fb 100k
Rg fb 0 47k
.subckt buf a out
Rb a out 1k
.ends
X1 out n1 buf
.end
"""

AFTER = """* LDO 反馈网络 v2：反馈电阻调值 + 新增前馈电容
Vin in 0 DC 1.2
Rf out fb 120k
Rg fb 0 47k
Cc out fb 2p
.subckt buf a out
Rb a out 1k
.ends
X1 out n1 buf
.end
"""


class TestPublicApiDemo(unittest.TestCase):
    """parse_text → diff → render_markdown 三步组合，输出可核对的变更报告。"""

    def setUp(self):
        self.before = parse_text(BEFORE, "before.sp")
        self.after = parse_text(AFTER, "after.sp")
        self.result = diff(self.before, self.after)
        self.kinds = sorted(c.kind for c in self.result.changes)

    def test_parse_both_versions(self):
        # 解析本身要成功（rc=3 的那类「读不了」在这里会直接抛/报错）。
        # 顶层器件含实例 X1，所以 v1 = 4、v2 = 5。
        self.assertEqual(len(self.before.top), 4)      # Vin / Rf / Rg / X1
        self.assertEqual(len(self.after.top), 5)       # 多了 Cc
        self.assertEqual(self.result.summary["device_added"], 1)

    def test_detects_one_added_and_one_param_change(self):
        self.assertEqual(self.kinds, ["device_added", "param_changed"])

    def test_exit_code_is_1_structural_difference(self):
        # 0 无差异 / 1 有差异 / 2 器件身份判不准 / 3 输入读不了
        self.assertEqual(self.result.exit_code, 1)

    def test_markdown_reports_the_two_changes(self):
        text = render_markdown(self.result, "before.sp", "after.sp")
        self.assertIn("Cc", text)
        self.assertIn("Rf", text)
        # 报告里参数显示为「原始写法 (归一化值)」，如 `120k (1.2e5)`，
        # 所以只断言完整片段，别断言裸数值。
        self.assertIn("120k (1.2e5)", text)

    def test_explain_adds_per_module_summary_and_advisory(self):
        text = render_markdown(self.result, "before.sp", "after.sp", explain=True)
        self.assertIn("按模块汇总", text)
        self.assertIn("风险提示", text)
        # 风险提示是启发式分诊，不是判定结论——这条口径不许被改掉
        self.assertIn("不是判定结论", text)


if __name__ == "__main__":
    unittest.main()
