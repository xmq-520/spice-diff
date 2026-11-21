# M1-codex（占位任务单，等 Codex 部填实）

id: M1-codex
部: Codex
交付: 解析 + 归一化 + 对齐 + diff 核心；CLI 与 JSON schema 落地（README 已冻结，照抄）
落点: src/spice_diff/ , tests/unit/          ← 必须是第一节归属表里本部的目录
前置: M0 已过（15:5x 实测达标）
出口条件: pair_a 零差异 且 退出码 0            ← 必须可用一条命令判定
自测命令: <待 Codex 填：在本机可逐字复制执行的那一条>
回滚: <待 Codex 填：本次变更涉及的文件清单>

状态: 未开工

## dsh 给 Codex 的两条环境提示（不是意见，是省时间）

1. **别用系统 Python 装包**：`C:\Python39` 的 site-packages 不可写、无 `wheel`、setuptools 58.1.0，
   `pip install .` 必报 `invalid command 'bdist_wheel'`。用本仓库的 `.venv`：
   `.\.venv\Scripts\python.exe -m pip install --no-index --no-build-isolation --no-cache-dir -q .`
   若需联网拉包：`$env:PIP_INDEX_URL='https://pypi.tuna.tsinghua.edu.cn/simple'`（pypi.org 直连在本机不通），
   并保留 `--no-cache-dir`（pip 的 wheel 缓存目录被沙箱拒写）。
2. **测试按标准库 `unittest` 写**：`.\.venv\Scripts\python.exe -m unittest discover -s tests/unit`。
   不要把 pytest 当硬依赖——PLAN.md 第 4 节这条已改口径。
