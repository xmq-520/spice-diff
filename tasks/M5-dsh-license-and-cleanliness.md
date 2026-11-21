# spice-diff — 17:29-17:44 MIT 落盘 + push 前洁净检查（臣 dsh）

## 一、MIT 已落盘（催了四遍的账结清）
陛下拍板 **MIT / 个人账号 / 版权人 XMQ**。臣执行：

1. Hermes 备好的 `shared\spice-diff\LICENSE`（`Copyright (c) 2026 XMQ`，21 行，MIT 全文）拷入仓库根。
2. `pyproject.toml:12` → `license = { text = "MIT" }`（原 `TBD`）。
3. commit **`92d2a2c`** `license(MT): MIT with copyright holder XMQ per owner's decision 11-21 17:29`（+21 / -2，2 files）。
4. 17:42 `git branch -m master main` —— **臣此前说「分支本来就是 main」不准确**；Hermes 那句 `git branch -M main` 这次是必要的，臣认这条。

现在 push 只需两条（陛下亲手）。`origin` 臣 17:47 已配好 = `https://github.com/xmq-520/spice-diff.git`，
所以网页建空库之后只剩 push 一条：
```powershell
cd C:\Users\hp\Documents\ClawChat\deepseek_harness\spice-diff
git push -u origin main
```

## 二、臣 17:27 说错了，OpenCode/Codex 纠正得对GitHub **不会**在 `git push` 时自动建库，推不存在的仓库只报 `fatal: repository not found`。
正确顺序：下载（含 `.git`）→ 网页建**空**库（不勾 README/.gitignore/license）→ HTTPS push，**密码用 PAT**。
臣 17:30 补的「`remote add` 后对 not found 答 `y` 让 git 代建库」**未实测**，只当加速选项，不作承诺。

## 三、push 前洁净检查（陛下授权臣执行，只读）—— 结论：可以推
| 项 | 范围 | 结果 |
|---|---|---|
| 密钥 `sk-` / `ghp_` / `github_pat_` | 32 个 `git ls-files` 跟踪文件 | **0 命中** |
| 同上 | **全历史 `git log -p --all`** | **0 命中** |
| 本机绝对路径 `C:\Users` | 跟踪文件 | 5 处（见下），**不阻塞** |
| `.pyc` / `.venv` / `pkgs/` / `build/` | `git ls-files` | 未跟踪（.gitignore 已挡） |

5 处本机路径（都是开发辅助，不进安装产物）：
- `PLAN.md:77` `:83`、`tasks/M0-dsh.md:19` —— 文档叙述；
- `tools/verify.ps1:27` —— 可被 `-Shared` 参数覆盖；
- `tests/unit/test_expectations_selfcheck.py:13` —— 可被环境变量 `SPICE_DIFF_SHARED` 覆盖；
- （Hermes 报的 `.venv` 里第三方包假阳性确实存在，但 `.venv/` 已 gitignore。）

要 GitHub 面上干净：v0.2 随 M1 一起换相对路径 + 读环境变量。**属臣的 tools/tests，臣随时可改——等陛下一个字。**

## 四、⚠️ 顺带查出臣自己的真回归（对外口径当场收回）
**现象**：干净 venv `pip install .` 现在**失败**：
```
Preparing metadata (pyproject.toml): finished with status 'error'
error: invalid command 'bdist_wheel'
```
**根因（三条实测）**：
1. 本机**任何 Python 都没有 `wheel`**：`C:\Python39\python.exe -c "import wheel"` → `ModuleNotFoundError`（系统 pip 26.0.1 / setuptools 58.1.0 / packaging 26.3，但没 wheel）。
2. 离线 `pkgs/` 只有 `setuptools-82.0.1` / `wheel-0.48.0` / `pytest-8.4.2`；而 `wheel-0.48.0` 要 `packaging>=24.0` —— **`packaging` 不在 pkgs/**，`--no-index` 装不上。
3. 外网补包两条路都堵：`pip download` 120s 无响应挂死（17:39、17:41 各一次，臣已 job_kill）。

**结论**：`license = MIT` 这一步本身是好的（构建日志有 `adding license file 'LICENSE'`），但 **16:04 臣把 `requires-python` 放宽到 `>=3.9` 后没重跑干净目录安装，埋了这个雷**。
⇒ **在重跑通过前，臣此前对陛下讲的「干净目录 `pip install` 成功」这句撤回**，Hermes 写安装说明也先别写这条。
**修法二选一**（臣本行的活）：① 把 `packaging` 的 py3-none-any wheel 想办法补进 `pkgs/`；② `[build-system]` 钉到会自带 bdist_wheel 的老 setuptools、绕开 `wheel` 依赖。

## 五、M1 现状（洁净检查顺手复测）
`shared\spice-diff\src` 17:42 仍 **False**；臣仓库 `src/spice_diff/` 仍只有 M0 占位 `cli.py`(16:04) + `__init__.py`(15:40)。
## 六、17:47-17:52 **更正：第四节那条「安装回归」是臣误判，现已当场修复并跑通**

**先说结论**：干净 venv 装包 **通过**（rc=0，`spdiff --version` → `spice-diff 0.1.0`），三条路径全过。
臣 17:44 报的 `pip install .` 失败**是真的报错，但根因和修法都写错了**——
第四节第 3 条「外网 `pip download` 120s 无响应挂死」**不成立**：那两次用的是 PowerShell 的 `Invoke-WebRequest`，
它在这台机上走系统代理才挂；换成 `python -m pip download` **5 秒就下完了**。
⇒ 教训同 `28ae7e1` 那条一致：**没实测过的「环境做不到」不能写成结论**，尤其不能据此对外收回一句已经成立的话。

**真正的原因**（只有一条，比臣原先写的简单）：本机系统 Python 3.9.13 的 setuptools 是 **58.1.0**，不带 `bdist_wheel` 命令；
`pkgs/` 里虽有 `wheel-0.48.0`，但它依赖 `packaging>=24.0` 而 `packaging` **缺件**，所以离线补装链断在这一个 wheel 上。

**修法（已做）**：`pip download` 取 `packaging-26.3-py3-none-any.whl` 补进 `pkgs/`（未跟踪，`.gitignore:14` 已挡，不进仓库）。
三个 wheel 的 `Requires-Python` 实测都是 `>=3.9`，与 `requires-python = ">=3.9"` 一致。`pyproject.toml` **未改动**。

**17:52 实测（新 `python -m venv`，三条路径）**：
| 命令 | 结果 |
|---|---|
| `pip install .`（默认，联网 build isolation） | **rc=0** `Successfully installed spice-diff-0.1.0` |
| `pip install --no-index --find-links <绝对路径>\pkgs .`（完全离线） | **rc=0**，`spdiff --version` rc=0 |
| 前置 `--upgrade pip setuptools wheel` + `--no-index --find-links pkgs --no-build-isolation .` | **rc=0** |

⇒ **Hermes 那条「pip install 先别写」的限制解除，可以写。** 两个必须带上的坑，写进安装说明：
1. `pip` 缓存目录会被沙箱拒（`WinError 5`）→ 一律带 `$env:PIP_NO_CACHE_DIR='1'`；
2. `--find-links` 必须写**绝对路径**——臣这次踩到了：`--find-links pkgs`（相对）+ `--no-build-isolation` 会**找不到 pkgs 又退回系统 setuptools 58.1.0**，
   复现出同一个 `invalid command 'bdist_wheel'`。写成 `--find-links "$PWD\pkgs"` 才对。
   （注：`pkgs/` 不进 git，所以陛下 clone 之后用不到它——clone 侧走默认那条 `pip install .` 即可，实测 rc=0。）

**另外两处对 Hermes 17:47 那条的实测更正（关系到 push 会不会被拒）**：
- 「先 `git config user.name/email`」这条**不必再设**：`git config user.name` → `xmq`，`user.email` → `2968768967@qq.com`（Hermes 17:46 那条命令已执行）。
  且 5 条 commit 里**只有 `92d2a2c` 作者是 `dsh <dsh@localhost>`**，另 4 条都是 `xmq <2968768967@qq.com>`。
- 「压成一条干净初始 commit」**有硬阻塞**：GitHub 对 push 做 **email 校验**，`dsh@localhost` 这类非法 email 会被 remote **直接拒推**
  （报错关键词 `push has been rejected because one or more commits contain invalid email addresses`）。
  ⇒ **不 squash，也得改那一条的作者**。改法是本地两条命令（重写历史，push 前做最干净）：
  ```powershell
  cd C:\Users\hp\Documents\ClawChat\deepseek_harness\spice-diff
  git rebase -i --root --exec "git commit --amend --no-edit --reset-author"
  ```
  臣**没有擅自动手**——这属于改历史，等陛下一个字，臣随时能办并复验。

## 七、17:52 M1 复测（本节最后一条，别漏）
`shared\spice-diff\src` 17:47 仍 **False**。臣仓库 `src/spice_diff/` 仍只有 `__init__.py` + 47 行占位 `cli.py`（`git ls-files src` = 2 个文件）。
Codex 第七次口头认领（17:46「继续把 src/ 最小实现落盘」），**落盘仍 0 字节，自 15:47 累计约 2 小时**。
① 死线 18:30 / ② Hermes 接手 / ③ 落进臣仓库 `src/spice_diff/`（只差 `core.diff()`）—— **等陛下点一条**。臣 18:10 看门照挂。

## 八、17:50 GitHub 账号被停用：臣的实测 + 一条要补的规矩
陛下第一个号（17:3x 那轮）被 GitHub 以违反条款停用，换 `xmq-520` 重注册。**这条和 push 有直接关系，必须说清：**

1. **旧号那边先停手**：Hermes/OpenCode 已说过——**别在同一浏览器来回登两个号**，也别拿旧号 token 再试 push。关联账号连坐是国内新号被停后申诉失败的第一大原因。
2. **本机凭据状态实测**：`git config --get-regexp credential` → 空；`gh` 不存在；`%USERPROFILE%\.ssh` 无 key。
   ⇒ 臣这侧**没有也不需要**任何 GitHub 凭据；token 只会出现在陛下输入的那一次弹窗里，不会落到任何文件或 commit（洁浄检查已扫 `ghp_`/`github_pat_` = 0，臣会在 push 后再扫一遍工作区）。
3. **PAT 权限取最小**：fine-grained token 只给 `spice-diff` 这一个仓库的 **Contents: Read and write** 就够推送；classic 勾 `repo` 是更宽的口子，没必要。**只建一个 token**——短时间连开多个 token 本身就是新号风控信号。
4. **`origin` 臣已配好**（`https://github.com/xmq-520/spice-diff.git`），`XMQ` 只在 `LICENSE` 署名里——OpenCode/Codex 这条纠正得对，署名和账号名不是一回事。
5. 若 `xmq-520` 也出现同样提示，**别再注册第三个号**：改推 GitLab / Codeberg 一行 remote 地址的事，代码和历史都不丢（臣可同步准备第二个 remote）。


