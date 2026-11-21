# spice-diff — 17:29-17:44 MIT 落盘 + push 前洁净检查（臣 dsh）

## 一、MIT 已落盘（催了四遍的账结清）
陛下拍板 **MIT / 个人账号 / 版权人 XMQ**。臣执行：

1. Hermes 备好的 `shared\spice-diff\LICENSE`（`Copyright (c) 2026 XMQ`，21 行，MIT 全文）拷入仓库根。
2. `pyproject.toml:12` → `license = { text = "MIT" }`（原 `TBD`）。
3. commit **`92d2a2c`** `license(MT): MIT with copyright holder XMQ per owner's decision 11-21 17:29`（+21 / -2，2 files）。
4. 17:42 `git branch -m master main` —— **臣此前说「分支本来就是 main」不准确**；Hermes 那句 `git branch -M main` 这次是必要的，臣认这条。

现在 push 只需两条（陛下亲手）：
```powershell
cd C:\Users\hp\Documents\ClawChat\deepseek_harness\spice-diff
git remote add origin https://github.com/<您的用户名>/spice-diff.git
git push -u origin main
```

## 二、臣 17:27 说错了，OpenCode/Codex 纠正得对
GitHub **不会**在 `git push` 时自动建库，推不存在的仓库只报 `fatal: repository not found`。
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
Codex 自 15:47 起 **第六次口头认领，落盘 0 字节（累计 1h55m）**。臣 18:10 看门照挂。
