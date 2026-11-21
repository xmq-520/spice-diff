# M6(dsh) — 18:10 看门实测记录

## 一句话
`shared\spice-diff\src` **18:10 仍不存在**，M1 解析器零落盘；除此之外臣这摊（MIT / push 前置 / 安装回归）全部就位，**只差 `src/` 一个文件**。

## 实测（18:10，全部刚跑，非复述）
| 项 | 命令 | 结果 |
|---|---|---|
| M1 落点 | `Test-Path 'C:\Users\hp\Documents\ClawChat\shared\spice-diff\src'` | **False** |
| 共享目录最新写入 | `Get-ChildItem -Recurse -File` 按时间倒序 | 最新一条 = `LICENSE`（**17:29:45**）；其余全部停在 15:33–15:35 |
| 臣仓库 `src/spice_diff/` | `Get-ChildItem` | 仍只有 `cli.py` 1864B + `__init__.py` 611B（M0 占位） |
| git 历史 | `git log --oneline` | 7 条：`9a693d3` / `4c8a6af` / `6175105` / `a805d68` / `48f4e7d` / `31204b5` / `f627145` |
| 工作区 | `git status --porcelain` | 干净（无未提交改动） |

> 注：臣仓库所有文件的 `LastWriteTime` 都是 **18:04:32**，而 commit message 里写的是 17:2x–17:5x。
> 说明这棵树在 18:04 被重建/重新 checkout 过（历史内容一致、`git status` 干净）。
> **不影响任何结论**，但说明「用文件时间戳判断谁在改」在这台机上不可靠——以后只认 `git log` 和内容。

## 已结清的账（本轮不再向陛下催）
- **许可证**：MIT 已落盘（`a805d68`，版权人 XMQ），`pyproject.toml` 不再是 `TBD`。
- **仓库归属**：个人账号 `xmq-520`，`origin` 已配好 = `https://github.com/xmq-520/spice-diff.git`。
- **干净目录 `pip install`**：三条路径 17:52 实测 rc=0（详见 `tasks/M5-...md` 第六节，17:44 那条误判已更正）。
- **push 前洁净检查**：全历史密钥 0 命中，可以推。

## 仍卡着的两件（都不是臣能自己动的）
1. **M1 解析器**：自 15:47 起 **2 小时 23 分、累计七次以上口头认领，0 字节落盘**。三条路等陛下点一条 —— ① 死线 / ② Hermes 接手 / ③ 落进臣仓库 `src/spice_diff/`（只差 `core.diff()`）。
2. **push 前的作者邮箱**：commit `92d2a2c` 作者是 `dsh <dsh@localhost>`，GitHub 会因非法 email **拒推**。改法（重写历史，等陛下点头臣才动）：
   ```powershell
   cd C:\Users\hp\Documents\ClawChat\deepseek_harness\spice-diff
   git rebase -i --root --exec "git commit --amend --no-edit --reset-author"
   ```

## 看门结论
M1 一落地，臣的五对样例脚本（`tasks/M4-dsh-cleanroom.md`，命令原样可抄）即刻全跑并回报。
