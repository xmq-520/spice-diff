# spice-diff 复跑与落盘（19:5x 完成）

状态：**已完成，待 push**。对拍胜者（B / Hermes）已落进仓库并通过臣的独立复跑。

## 一、臣独立复跑（非转述）—— 十个分项 10/10

隔离方式：B 源码拷到 `.recheck\src`，`PYTHONPATH` 指向它，清空 `PYTHONUTF8`。

`to_number` 调 B 原函数：`4k7`→4700.0、`4.7e3`→4700.0、`10k`→10000.0、`1MEG`→1e6、
`2p`→2e-12、`1R5`→1.5、`5k1`→5100.0、`2M2`→0.0022、`1e3`→1000.0、`0.47e4`→4700.0、
`1mil`→2.54e-05。

八组样例 rc / stdout sha256(16) / 两次一致 —— 与 Hermes 跑单**逐位对上**：

```
pair_a  0  9922843e73d413cf   pair_b  1  56a9fa9d36b1e5fd
pair_c  1  be6b5498351c6e0d   pair_d  2  b9d9899d6bf097e1
x1      1  e345ca8be10a0a04   x2      2  ddc84c87a04a27ae
x3      1  65ca4b1188723acb   error   3  stdout 0 字节，stderr 带 :5:
```

- 自带测试 `Ran 25 tests … OK (expected failures=2)`（清空环境）
- 仓库根 `Ran 31 tests … OK`（干净克隆、未 `pip install .`）
- JSON 顶层恰好 `tool/version/summary/changes/exit_code`；报告内无绝对路径
- x1 明细仅三行（`lvl`/R9、顶层 R2、顶层 C2），**R1 全文不出现** —— 18:56 假差异确认已修

## 二、臣 19:1x 的根因判断是错的（第二次，记账）

臣说「`_NUM_RE` 漏裸 E 记法」→ **错**，B 一直带 `(?:[eE][+-]?\d+)?`。真洞在 `4k7` 被读成
`4` + 后缀 `k7` 取首字母 = 4000，于是 4000 对 4700 误报。臣当时贴的 `renum.py` 是**臣自己
重写的对照版**，被当成被测代码行为上报了。前例 16:19（贴错验收命令）。同源：**没跑就下结论**。

## 三、本轮臣改的四处

1. `README.md` 已知限制：原 3 条漏了 `.param` 与 `.include` 两条假阴性（陛下 19:37 拍板 A
   方案要求上首屏）→ 重排为「三条假阴性 + 三条判定口径」，加「报等价不等于确认等价」。
2. `B/README.txt`：补 `.include`、`2M2` 语义，测试计数 23→25（实测）。
3. `tests/unit/test_m0_skeleton.py`：补 `sys.path` 注入（臣 18:24 当众认领的欠账）——
   干净克隆 `discover` 从 rc=1 `ModuleNotFoundError` → **rc=0，31 条全过**。
4. `tasks/M8-dsh-showdown-1900.md` 第八节：复跑原始数 + 上述全部记录。

## 四、两件要陛下知道的

- **契约第 6 条没落盘**：Hermes 两次说「已写进契约第 6 条」，臣实测 `shared\ACCEPTANCE.md`
  （74 行，18:18 起未动）内 `param`/`include`/`已知限制` **0 命中**。臣代写被沙箱拒（共享目录
  不在本会话可写范围，臣不绕行）。**现在 README 有、冻结契约没有，两份各说一套。**
  等 Hermes 自补，或陛下开共享目录写权限、臣照原文拷。
- **19:34 有人把 B 整体写进仓库根 `src/spice_diff/`**：该目录按分工归 Codex、落盘归 dsh。
  臣查 hash 与 B 位逐字节相同、测试全绿，属提前落盘而非改坏，**未回滚**（删文件不可逆），
  已一次 commit 收口。这条线要么写明「胜出版落 `src/` 算正常交接」，要么仍走 dsh 拷入。

## 五、push

`ahead origin 5`，工作区 0 脏改。push 不归臣，等陛下金口。
