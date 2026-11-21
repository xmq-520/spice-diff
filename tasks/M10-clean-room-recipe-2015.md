# M10 · 干净复跑「唯一正确跑法」+ 臣 19:5x 两处误报更正（20:1x，dsh 实测）

## 0. 本文所有数字均为 20:1x 本机实跑，非转述。

## 1. 更正臣 19:5x 的两处误报

| 臣 19:5x 说 | 实测 |
|---|---|
| 补空 `__init__.py` 后全量 `Ran 41 tests OK (expected failures=2)` | **假绿**。清空 `PYTHONPATH` 后原样拷入照旧 `Ran 41 FAILED (failures=6, unexpected successes=2)` |
| 根因在 `test_edges.py:18` | 实为 **L17** |

**假绿机制**：同一串命令里前一步已 `$env:PYTHONPATH="$T\src"`（指向 %TEMP% 那份检出），
后面 discover 起的子进程靠**继承来的 PYTHONPATH** 找到了 `spice_diff`，
于是 `test_edges.py` 自己那行算错的 `SRC` 根本没起作用。
→ 教训：**报「绿了」之前先问是不是继承了环境；对照实验一次只清一个变量。**

## 2. 唯一正确跑法（可复现，逐步照抄）

```powershell
$R = "C:\Users\hp\Documents\ClawChat\deepseek_harness\spice-diff"
$T = "$R\.m10-wt"
git -C $R worktree add --detach $T 057bbe9

$env:PYTHONPATH = ""          # ← 关键：必须显式清空
$env:PYTHONUTF8 = $null

New-Item -Force "$T\tests\blackbox\__init__.py" -ItemType File | Out-Null
Copy-Item "$R\tools\spice-diff-showdown\B\tests\test_edges.py" "$T\tests\blackbox\test_edges.py"
```

⚠️ `%TEMP%` 本轮**不可写**（`could not create leading directories ... Permission denied`），
worktree 必须开在仓库内（`.m10-wt`），收尾用
`git -C $R worktree remove --force $T; git -C $R worktree prune`。

## 3. 20:1x 实测（L17 按甲案改好后）

`Ran 41 tests ... OK (expected failures=2)`，八组对拍（`PYTHONPATH=$T\src`）：

| 组 | rc | stdout sha256 前 16 |
|---|---|---|
| pair_a | 0 | `ceef574186f30b86` |
| pair_b | 1 | `735f5f24dae71d5e` |
| pair_c | 1 | `b6cb044f9763dcd3` |
| pair_d | 2 | `e60abba0bebd6f3c` |
| x1 | 1 | `5dc859691e81a219` |
| x2 | 2 | `fb57e88832ccf188` |
| x3 | 1 | `d25951742940a08a` |
| error（单参数） | 3 | 0 字节 |

**退出码与 19:5x 逐组一致**；sha256 与 19:5x 那串不同 —— 臣今日在仓库原样
（无 test_edges）用同法重跑，得到的就是上表这串，故**以本表为准**，
19:5x 的 sha 取自另一种取字节方式（疑多一个行尾），作废。

## 4. 样例文件的真实位置（别再猜）

- pair_*：`tools/spice-diff-showdown/B/examples/pair_*_{before,after}.sp`
- x1-x3：`tools/spice-diff-showdown/extras/x*_{before,after}.sp`（`tests/functional/extras/` 亦有一份）
- 报错样例：`tools/spice-diff-showdown/B/examples/error_bad_syntax.sp`
- **不存在** `tests/functional/pairs/`，也没有 `before.sp`/`after.sp` 这种裸名。

## 5. 仓库收尾状态（20:1x）

`HEAD 057bbe9`｜`main`｜`ahead origin 6`｜脏改仅一项未追踪
`tools/spice-diff-showdown/test_edges.orig.py`（臣留的未修原件备份，可删）。
`tests/blackbox/` 在 commit 里**不存在**，tracked 文件 0 个 → **缺口仍开着**。
