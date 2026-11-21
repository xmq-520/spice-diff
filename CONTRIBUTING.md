# 贡献指南

## 环境

- Python 3.9+（CI 覆盖 3.9 / 3.10 / 3.11 / 3.12 × Linux / Windows）
- 跑测试：`python -m unittest discover -s tests -t .`
- 打包：`pip install .`（需要 `setuptools >= 61`，否则 `[project]` 表被忽略、装出 `UNKNOWN-0.0.0` 且没有 `spdiff` 命令）

## 目录

```
src/spice_diff/parse.py   解析：续行、注释、.subckt 层次、器件子集
src/spice_diff/core.py    归一化、配对、差异分类、渲染
src/spice_diff/cli.py     argparse 与退出码
tests/functional/         端到端：真跑 CLI，断言退出码与输出
tests/blackbox/           边界写法：CRLF、BOM、制表符、.param、.include
examples/                 黄金样例与期望输出
docs/                     用法、设计、已知限制
```

## 加一条测试的规矩

1. **必须真跑 CLI**（子进程），不许只测纯函数就宣布功能可用。
2. **断言退出码 + 输出内容**，二缺一不算过。只断言退出码会在 `ModuleNotFoundError` 时假绿。
3. 子进程显式 `encoding="utf-8"` 并设 `PYTHONUTF8=1`，别依赖本机 locale。
4. 已知缺陷用 `unittest.expectedFailure` 钉住，**不要为了让测试变绿删掉它**；修好后它会变成 unexpected success，那时再删装饰器。
5. 测试要能在多种目录布局下跑（仓库 `tests/`、对拍目录），路径用向上查找，不要写死层数；找不到实现就当场抛错，**拒绝伪通过**。

## 改行为之前

先改 `docs/` 或 README 里的契约描述，再动代码。契约是判据，代码是它的实现，不是反过来。

## 提交

- 一个 commit 一件事，message 写清「改了什么、为什么」。
- 不提交 `__pycache__`、`build/`、`*.egg-info`、`.venv/`。
