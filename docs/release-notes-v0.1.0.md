# v0.1.0 发布说明

**定位：技术预览（technical preview）。可公开试用、可提 issue；不是稳定成品。**

## 这个版本是什么

`spdiff BEFORE.sp AFTER.sp` —— 两份 SPICE 网表之间的**结构**变更报告。
Markdown 给人看，`--json` 给 CI 看；退出码 0 / 1 / 2 / 3 四态。

- 纯标准库，Python 3.9+，零运行时依赖
- `pip install .` 后得到 `spdiff` 命令；也可 `PYTHONPATH=src python -m spice_diff.cli`
- 保留 `.subckt` 层次；单位归一（`4k7` = `4.7k` = `4.7e3` = `4700`）；顺序无关
- 身份不可唯一确定时输出 `uncertain` + 候选，退出码 2，**不猜 refdes**
- 同一对输入两次运行，输出字节一致

## 明确不做什么

- **不做 LVS，不做网表等价证明。** 它不是等价性检查器。
- **`rc=0` 不等于「两份网表等价」**，只等于「没找到结构差异」。

## 三类已知假阴性（v0.1 未修）

| 情形 | 行为 |
|---|---|
| 只改 `.param` 值，器件行引用参数名 | 报 rc=0 |
| `.include` 目标不同 / 内容不同 | 报 rc=0 |
| 分析语句（`.tran` / `.ac` / `.dc` / `.ic`）改动 | 报 rc=0 |

三条都用 `unittest.expectedFailure` 钉在 `tests/blackbox/test_edges.py` 里，修好后会变成
unexpected success，提醒维护者去掉装饰器。详见 [limitations.md](limitations.md)。

## 验证情况（本版已知的全部证据）

- `python -m unittest discover -s tests -t .` → 41 条通过（2 条 expectedFailure）
- 五组黄金样例退出码：`pair_a 0` / `pair_b 1` / `pair_c 1` / `pair_d 2` / `error 3`（stdout 为空）
- 三组加赛样例：`x1 1` / `x2 2` / `x3 1`
- CI：GitHub Actions，Python 3.9–3.12 × Ubuntu/Windows，跑测试、装包、样例退出码、输出确定性

**缺口（明确写在发布页上）**：以上全部是自造样例，**尚未用真实产线网表验证**；
规模已实测到 2 万只器件（0.43 秒，零误报），但仍是自造扁平网表。

## 装

```bash
pip install .          # 需要 setuptools >= 61
spdiff --version       # spice-diff 0.1.0
```

## 下一版

v0.2：`.include` 展开、`.param` 求值、分析语句变更列为 `uncertain`——即上面三类假阴性。
