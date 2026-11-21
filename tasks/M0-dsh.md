--- M0-dsh.md ---
id: M0-dsh
部: dsh
交付: 目录骨架 + git init + pyproject.toml（入口 spdiff）+ setup.py 兼容层 + tools/verify.ps1 空跑 + PLAN.md
落点: 全仓库骨架（本部所有）；src/spice_diff/{__init__.py,cli.py} 为 M0 占位，M1 起归 Codex
前置: 无
出口条件: `pip install .` 成功 且 `spdiff --help` 退出码 0
自测命令: .\.venv\Scripts\python.exe -m pip install --no-index --no-build-isolation -q . ; .\.venv\Scripts\spdiff.exe --help
回滚: 删除整个 spice-diff/ 目录即完全撤销（仓库独立于共享目录，未污染他人文件）

状态: 已过（15:5x 实测：spdiff --help 退出码 0，usage 正常打印）

## M0 实测记录（可复核）

- 本机 `C:\Python39\python.exe` = 3.9.13；`git` = 2.55.0；无 `python3`。
- 系统 site-packages 不可写、无 `wheel`、setuptools 仅 58.1.0（无 PEP 643）→ 直连 pip install 必报 `invalid command 'bdist_wheel'`。
- **pypi.org 直连不通**（TLS「基础连接已经关闭」），**清华镜像可达**：`PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`。
- 已建 `.venv`（`spice-diff\.venv`），内装 setuptools 82.0.1 + wheel 0.48.0；本目录 `.gitignore` 已排除。
- 坑：pip 写 wheel 缓存 `c:\users\hp\appdata\local\pip\cache\wheels` 被沙箱拒（WinError 5）→ 必须 `PIP_NO_CACHE_DIR=1` 或 `--no-cache-dir`；且必须 `--no-build-isolation`，否则 pip 会去 pypi.org 拉隔离构建环境而挂死。
- 因此本仓库保留 `setup.py` 兼容层（元数据仍以 `pyproject.toml` 为单一来源），供 3.9 + 老 setuptools 环境使用。
