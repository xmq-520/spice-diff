# ④ 对拍 · 裁判底账（dsh，18:20 起）

陛下 18:19 定：**方案 ④**，Codex 与 Hermes 同写，19:00 五组样例对拍，通过多者采用。臣任裁判，不参赛。

## 18:20 开赛前实测基线（不是转述）

| 项 | 实测 |
|---|---|
| `shared\spice-diff\src` | **False**（第九次确认，自 15:47 已 2h33m，落盘 0 字节） |
| `shared\spice-diff\` 内容 | `examples` / `tests` / `ACCEPTANCE.md` / `architecture.svg` / `LICENSE` / `PLAN.md` / `README.md` |
| 臣仓库 HEAD | `a9099d7`，工作区 0 脏改，`ahead of origin = 0` —— **本地与远端已同步，Hermes 说的「领先 4 条」已被推平** |

## 关于 push：此项已结清

- OpenCode 18:2x 实测 `[ahead 4]`、Hermes 18:2x 实测「远端停在 `9a693d3`、本地 `a9099d7`」——**两条都对，只是各自时刻不同**；臣 18:20 复测 `ahead = 0`，说明中间那次 `git push` 已经跑完。**README 现在在远端。**
- 结论：push 这条不再有任何待办，陛下不用再敲命令。

## 臣 18:20 落盘

- `tools\spice-diff-showdown\SCORE.md` —— 对拍规程 + 10 分计分表 + 判负红线 + 裁判承诺（**已 commit**）
- `tools\spice-diff-showdown\A\`（Codex 交付位）、`B\`（Hermes 交付位）—— 空目录
- 本文件

## 对计分表的一处主动说明（防赛后扯皮）

Hermes 要求「黄金样例测试必须断言 rc != 3」——**臣认下，并且已经加进第 1/2/3/4 项**：那四项要求的是**具体退出码 + 具体差异内容**，`rc=3` 一律记 0 分。也就是说本表里 `rc=3` 永远拿不到分，`error_bad_syntax` 那 1 分要求「报错含行号或文件名」，占位桩的 `core not implemented yet` 过不了。

Hermes 另一条（干净克隆里 `unittest discover` 报 `ModuleNotFoundError`）是**臣的文件、臣的欠账**，与对拍无关，臣 19:00 后单独修（`tests/conftest` 式 `sys.path` 注入或 README 明写 `pip install -e .`），不占对拍时间。

## 19:00 之后

胜者代码由臣拷进 `src/spice_diff/` → 全新 venv `pip install .` → 五组样例 + 确定性 + JSON 契约复跑 → 数字贴群 → commit。输的那版留档不删。
