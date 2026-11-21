# M4-dsh-cleanroom — 干净目录复跑（每轮 Codex 交付后重跑）

状态：进行中（M0 已过，M1 未交，e2e 判败等待 M1）

## 上一轮结果（16:19，对当前 src/ = M0 占位版）

环境：本机 C:\Python39\python.exe 3.9.13；临时目录 %TEMP%\spd-m4c-161912 新建 venv；
`pip install --no-index --find-links pkgs .` 成功（EXIT=0，wheel 进本地缓存，不碰用户 site-packages）。

| 检查 | 期望 | 实测 | 判定 |
|---|---|---|---|
| `spdiff --version` | 打印版本 | `spice-diff 0.1.0`，rc=0 | 过 |
| `spdiff pair_a_before pair_a_after` | 退出码 0（零差异） | rc=3 `core not implemented yet (M1, Codex)` | **败（M1 未交付）** |
| 缺参数 | 退出码 3 | rc=3 + usage | 过 |

结论：**M4 的 e2e 目前判败，败因不是假阳性，是 src/ 仍是臣 M0 的占位入口，核心比对无人实现。**
M1（Codex）落盘后本节全部重跑，pair_a/b/c/d + error 五对逐条对。

## 踩坑记录（写给 CI 和其他部）

1. `pip install .` 必须**先 cd 进仓库根目录**再跑（README 写法正确）；在别处跑会报 "Directory '.' is not installable"。
2. 本机 pip 缓存 `%LOCALAPPDATA%\pip\cache` 有目录 `WinError 5 拒绝访问`，构建 wheel 时直接失败。
   绕法：`$env:PIP_CACHE_DIR = <临时目录>\pipcache` 后再装。CI 里同理设 PIP_NO_CACHE_DIR=1 也行。
3. 断网安装可用：`pkgs/` 已备 wheel（setuptools/wheel/pytest），`--no-index --find-links pkgs` 即可。

## 自测命令（原样可跑）

```powershell
$t = Join-Path $env:TEMP ("spd-m4-" + (Get-Date -Format HHmmss))
New-Item -ItemType Directory $t | Out-Null
python -m venv "$t\venv"
$env:PIP_CACHE_DIR = "$t\pipcache"
cd <repo 根目录>
& "$t\venv\Scripts\python.exe" -m pip install --no-index --find-links pkgs .
& "$t\venv\Scripts\spdiff.exe" examples\pair_a_before.sp examples\pair_a_after.sp   # 期望 rc=0
& "$t\venv\Scripts\spdiff.exe" examples\error_bad_syntax.sp                          # 期望 rc=3（缺一参）
```
