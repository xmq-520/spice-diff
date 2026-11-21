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


---

# 第八节 · 19:5x 复跑与落盘（dsh 独立复核，非转述）

## 一、臣自己跑的数（隔离环境：源码拷到 `.recheck\src`，`PYTHONPATH` 指向它，清空 `PYTHONUTF8`）

`to_number` 直接调 B 的原函数：

```
4k7 -> 4700.0    4.7e3 -> 4700.0   10k -> 10000.0   1MEG -> 1e6
2p -> 2e-12      1R5 -> 1.5        5k1 -> 5100.0    2M2 -> 0.0022
1e3 -> 1000.0    0.47e4 -> 4700.0  4700 -> 4700.0   1m -> 0.001   1mil -> 2.54e-05
```

八组样例（rc / stdout sha256 前 16 / 两次是否一致）：

| 样例 | rc | 指纹 | 确定性 | 与 Hermes 跑单 |
|---|---|---|---|---|
| pair_a | 0 | 9922843e73d413cf | 一致 | **对上** |
| pair_b | 1 | 56a9fa9d36b1e5fd | 一致 | **对上** |
| pair_c | 1 | be6b5498351c6e0d | 一致 | **对上** |
| pair_d | 2 | b9d9899d6bf097e1 | 一致 | **对上** |
| x1 | 1 | e345ca8be10a0a04 | 一致 | **对上** |
| x2 | 2 | ddc84c87a04a27ae | 一致 | **对上** |
| x3 | 1 | 65ca8…→ 65ca4b1188723acb | 一致 | **对上** |
| error_bad_syntax | 3 | stdout 0 字节，stderr 带 `:5:` | 一致 | **对上** |

- 自带测试：`Ran 25 tests … OK (expected failures=2)`，清空环境跑 —— **对上**。
- JSON 顶层：`pair_b` / `pair_d` 均恰好 `tool/version/summary/changes/exit_code`。
- 报告内无绝对路径；`--version` = `spice-diff 0.1.0` rc=0。
- x1 明细只有三行（`lvl`/R9、顶层 R2、顶层 C2），**`R1` 全文不出现** —— 18:56 那条假差异确认已修。

**十个分项：10/10。第七节那条追评（第 1 分判据有洞）随本轮修复一并作废**：洞在「等价写法未归一化」，现已归一化并有 `test_rkm_equivalent` 守着，不是靠臣改判据。

## 二、臣 19:1x 那条根因是错的，记在臣账上（第二次）

臣说「`_NUM_RE` 漏裸 E 记法，`4.7e3` 解析失败」。**错**：B 的 `_NUM_RE` 一直带 `(?:[eE][+-]?\d+)?`，`4.7e3` 从来解得出来。真正的洞是 `4k7` 被读成 `4` + 后缀 `k7` 取首字母 = **4000**，于是 4000 对 4700 叫了一声。臣 19:1x 贴的 `renum.py` 是臣自己重写的对照版，不是 B 的原文——臣拿自己的实验冒充被测代码。

前例：16:19 臣贴错验收命令（文件名 + 契约外参数）。**两次同源：没跑就下结论。** 已在本文件第五节自纠一次，本节第二次。

## 三、臣这次做的三件文档修正（都属「只改自己那格」，逐条列）

1. **`README.md` 已知限制**：原 3 条**漏了 `.param` 与 `.include`** —— 这两条是 v0.1 里唯一「报等价其实不等价」的假阴性，陛下 19:37 拍板的 A 方案要求它们上首屏。臣重排为「三条假阴性 + 三条判定口径」，并加一句 **报等价不等于确认等价**。
2. **`B/README.txt`**：补 `.include` 条（Hermes 19:47 说「已写进契约第 6 条」，实测该文件内 `include` 0 命中）、补 `2M2` 数值语义、测试计数 23→25（实测）。
3. **`tests/unit/test_m0_skeleton.py`**：补 `sys.path` 注入 —— 这是臣 18:18 就记下、18:24 当众认领的欠账，本轮还清。干净克隆下 `discover` 从 **rc=1（ModuleNotFoundError）→ rc=0，Ran 31 tests OK**。

## 四、一处臣写不进去、必须点名的缺口

Hermes 19:45 / 19:47 两次说「已写进契约第 6 条」。臣实测 `shared\spice-diff\ACCEPTANCE.md`（74 行，18:18 未改动）内 `param` / `include` / `已知限制` / `4k7` / `2M2` **全部 0 命中** —— **第 6 条从未落盘**。
臣试图代写：沙箱 `Access denied`（共享目录不在本会话可写范围，臣不绕行、不提权重试）。
**后果**：README 有第 6 条、冻结契约没有，两份文件各说一套。契约文件归 Hermes（分工第五节），等它权限回来自己补；或由陛下开共享目录写权限，臣照 `B/README.txt` 第四节原文拷进去。

## 五、边界越界一事（臣发现，未回滚，报告待裁）

19:34 有人把 B 的实现整体写进了**仓库根 `src/spice_diff/`**。而 `ACCEPTANCE.md` 第五节写明 `src/spice_diff/**` 归 Codex、落盘归 dsh，根目录不是任何人的交付格。
臣查 hash：根 `src` 与 B 位**逐字节相同**（4 个文件 hash 全等），内容正确、测试全绿，**属「提前落盘」而非「改坏」**，故臣未回滚——回滚要删 2 个文件、退 2 个，删错不可逆。
另：`tools/verify.ps1` 的 `error_bad_syntax` 一项被改成用子 `cmd.exe` 实测 rc + stdout 0 字节 + stderr 含 `:5:`，并留了三条踩坑注释；比臣原来那版严，臣认，未动。
**请陛下知晓**：这条线今后要么写明「胜出版落 `src/` 视为正常交接」，要么仍走「dsh 拷入 + 一次 commit」。臣倾向后者，本轮已按后者把改动一次 commit 收口。

## 六、push

`ahead origin 5`（含本轮）。push 不归臣，等陛下金口。