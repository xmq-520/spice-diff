# spice-diff · dsh 部执行计划（M0–M4）

状态：**已定案（4:0）→ 开工（陛下 15:12 已点头）**。
契约为 `README.md`（Hermes 部，v0.1 已冻结）；本文件只管「谁在什么时候交出什么、什么算过」。

## 0. 四条硬约束

1. 契约以 `README.md` 为准；改契约 = Hermes 改文件 + 群里知会一次。任何部门不得单方面改口径。
2. 各干各部，**只准指正，不准代改他人文件**。
3. 本机 Python **3.9.13**（`C:\Python39\python.exe`，无 `python3`）。禁 `X | None` / `list[str]` / 3.10+ 语法。
4. 本机**无 GitHub 凭据**、无 `gh`。全程本地 commit，最后由陛下亲手建仓库 + push 一次。

## 1. 目录归属

**dsh 建并拥有**（M0 一次建齐，避免二次挪动）：

```
src/spice_diff/   tests/unit/   tests/golden/   tests/blackbox/
pyproject.toml    setup.py      .gitignore      LICENSE         CHANGELOG.md
tools/verify.ps1  tasks/        PLAN.md(本文件)
```

Codex 独占 `src/spice_diff/` 与 `tests/unit/`；OpenCode 独占 `tests/golden/`、`tests/blackbox/`；
Hermes 独占 `README.md`、`examples/`、`architecture.svg`。
`pyproject.toml` / `setup.py` 归 dsh：Codex 的构建配置需求以群里提意见的方式提出。

## 2. 阶段与出口条件

| 里程碑 | 负责 | 交付 | 出口条件（不满足不得进下一步） |
|---|---|---|---|
| **M0** | dsh | 目录骨架 + git init + `pyproject.toml`（入口 `spdiff`）+ `verify.ps1` 空跑；`PLAN.md` | `pip install .` 成功、`spdiff --help` 可执行 |
| **M1** | Codex | 解析 + 归一化 + 对齐 + diff 核心；CLI 与 JSON schema 落地（README 已冻结，照抄） | `pair_a` 零差异、退出码 0；**出现任何一条差异即判假阳性，直接判败** |
| **M2** | Codex | `pair_b` 对黄金输出 + model 比较（Hermes 已裁决保留）+ `.subckt` 层级 | 与 `expected_b.md` 逐条对上，**方向反了也算败** |
| **M3** | OpenCode | 刁钻 fixture + 黑盒验收报告（不看源码） | 逐例 pass/fail + schema 合规 + 退出码；问题退回 Codex 修，不代改 |
| **M4** | dsh | 干净临时目录 `pip install .` + **照 README 逐字敲一遍** | README 里有一条命令跑不通即算 dsh 没过 |
| **M5** | Hermes | 发布文案 / 项目页 | 不写没验过的话 |

**并行**：M3 的样例编写与 M1/M2 同时开工，仅黑盒执行等 M2。
**Hermes 补的 `uncertain` 样例**：落在 `examples/`，属 Hermes 部，作为 M2 的附加对拍输入（契约第 3 节已定 `uncertain` 语义，无需等 Codex）。

## 3. 判负口径（三方统一，不各说各话）

- `pair_a` 出任何差异 = 假阳性 = 败。
- `pair_b` 与 `expected_b.md` 逐条对，方向反了 = 败。
- JSON 字段以 README 的 v0.1 schema 为准，**加字段即败**（破坏确定性断言）。
- 同一对输入两次运行输出字节不一致 = 败。
- `uncertain` 时退出码必须为 2，不得为求绿灯而硬凑映射。

## 4. 当前阻塞与解法（15:12 实测）

- ~~**`pytest` 未安装**~~ → **已解（15:4x）**：清华镜像可达，`pip download` 拉到 wheel/setuptools；`.venv` 内 setuptools 82.0.1 + wheel 0.48.0 就绪。测试仍按标准库 `unittest` 写（`python -m unittest discover`），pytest 不作为硬依赖。
- 共享目录 **无 git 仓库**（已实测：`not a git repository`）。M0 在 `shared/spice-diff/` 建库，`LICENSE` 待陛下选定许可证后补。
- 仓库归属 / 许可证（Apache-2.0 vs MIT）/ 谁 push：仍等陛下。三项**不阻塞** M0–M4。

## 5. 陛下 15:12 那道旨里被读漏的半句

原文是「制定好**计划** **和任务的形式**」——两件事。契约（Hermes）管"做什么"，本文件第一节管"活落在谁的目录"，**第五节管交活的统一形式**。三家都说了"规则草案 + 小型可回滚变更 + 测试结果"，但没落成模板；不统一，M3/M4 的交叉验收就没法机械地判。

**任务单模板**（每条任务一张，写在 `tasks/` 下，文件名 `M<里程碑>-<部门>.md`）：

```
id: M1-codex
部: Codex
交付: 解析 + 归一化 + 对齐 + diff 核心
落点: src/spice_diff/ , tests/unit/          ← 必须是第一节归属表里本部的目录
前置: M0 已过
出口条件: pair_a 零差异 且 退出码 0            ← 必须可用一条命令判定
自测命令: <在本机可逐字复制执行的那一条>
回滚: 本次变更涉及的文件清单（小型可回滚 = 一句话说清撤掉哪几个文件）
```

**状态只有四个词**：`未开工` / `进行中` / `待验收` / `已过`。验收人只认「出口条件」和「自测命令」两项，其余不作数。

## 6. 阻塞（15:5x 更新）

- **M0 的共享目录写入阻塞 → 臣按出路 ③ 自行推进，不再等批**：
  `C:\Users\hp\Documents\ClawChat\deepseek_harness\spice-diff\` 已是带 git 历史的独立仓库，
  骨架 / `pyproject.toml` / `setup.py` / `tasks/` / `.venv` 全部就位，M0 出口条件实测达标。
  **本仓库即为工作副本**；`shared\spice-diff\` 仍是 Hermes 的 `README.md`、`examples/` 与
  OpenCode 的 `tests/golden`、`tests/blackbox` 所在地。合并点由陛下一句话决定（臣搬过去，或陛下取走），
  在此之前**不搬**——搬一次即产生两份真相，违背"只准指正不准代改"。
- **跨目录取件方式（已实测可行）**：`shared\` 在本机可读（读不受沙箱限制，只有限写）。
  故 `tools/verify.ps1` 直接从 `$env:SPICE_DIFF_SHARED`（默认 `C:\Users\hp\Documents\ClawChat\shared\spice-diff`）
  读 `examples/` 跑 e2e 对拍。**这是臣单方面能跑的验收面，不需要任何人挪文件。**
- `examples/` 已由 Hermes 扩到 **a/b/c/d 四对 + 反例 `error_bad_syntax.sp`**（15:21 实测），`expected_c.md` 要求 `scope=buf` 不得展平。M1/M2 的对拍面比臣写计划时大一圈，已同步。

## 7. 变更日志

- 15:12 dsh：M0 开工，本计划生效。
- 15:22 dsh：补第 5 节「任务的形式」；记 M0 提权被驳回与三条出路；同步 `examples/` 已扩至四对。
- 15:4x dsh：**走第 6 节出路 ③**——在 `deepseek_harness\spice-diff\` 建独立 git 仓库；`.venv` 工具链装齐，`pip install .` 与 `spdiff --help` 已通，M0 出口条件达标。
- 15:5x dsh：`tools/verify.ps1` 落地（从共享目录读 `examples/` 跑 e2e）；`tasks/M0-dsh.md`（已过）、`tasks/M1-codex.md`（占位待 Codex 填）就位。
