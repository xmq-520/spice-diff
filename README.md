# spice-diff

![status](https://img.shields.io/badge/status-v0.1.0-orange)
![license](https://img.shields.io/badge/license-MIT-blue)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![deps](https://img.shields.io/badge/dependencies-none-success)

**两版 SPICE 网表之间的结构变更报告。**

改版之后，两份网表到底差在哪？器件换了值、删了一个、多了一根连接、改在哪个子电路里——
一条命令出报告，Markdown 给人看，JSON 给 CI 看。

```bash
$ spdiff old.sp new.sp

# spice-diff：old.sp → new.sp

## 变更摘要

- 器件新增：1　器件删除：1　参数变化：1　连接变化：0　模型变化：1　不确定：0

## 明细

| 类别 | 位置 | 器件 | 变更前 | 变更后 |
|---|---|---|---|---|
| device_removed | 顶层 | C1 | C1 n1 0 10p | — |
| device_added | 顶层 | D2 | — | D2 0 out DMOD |
| model_changed | 顶层 | DMOD | D(IS=1e-14 N=1) | D(IS=1e-14 N=1.05) |
| param_changed | 顶层 | R2 | 2k (2e3) | 3k (3e3) |

退出码 1（存在结构差异）。
```

---

## ⚠️ 先读这一段：它不是等价证明工具

spice-diff 是**结构差异报告器**，不是 LVS，不做网表等价证明。
v0.1 有三类**假阴性**——工具报「无结构差异」，而两份网表其实不等价：

| 情形 | v0.1 行为 | 说明 |
|---|---|---|
| 只改 `.param` 值，器件行引用参数名 | 报 rc=0 | 不做表达式求值，参数名只按字符串比 |
| `.include` 指向不同文件，或包含内容不同 | 报 rc=0 | 不展开 include |
| 改分析语句（`.tran` / `.ac` / `.dc` / `.ic`） | 报 rc=0 | 分析语句不参与比对 |

**所以：`rc=0` 只能读成「没找到结构差异」，不能读成「两份网表等价」。**
要做等价确认，请走仿真或 LVS。详见 [docs/limitations.md](docs/limitations.md)。

## 它擅长什么

- **改版审阅**：PR 里逐条看「这一版到底动了什么」，而不是在几千行 `git diff` 里捞。
- **ECO 核对**：改完手工确认「只动了 R2 和 C5」这类断言。
- **IP 交付比对**：客户拿到的网表与签过的版本是否一致。
- **手改 vs 脚本改**：网表最常出的错就是数字打错、单位后缀打错。
- **CI 门禁**：输出字节级确定，可直接断言退出码。

关键差别在**它懂 SPICE**：

- 单位归一：`4k7` = `4.7k` = `4.7e3` = `4700`；`1MEG` 是兆，`1m` 是毫。
- 语义归一：行序、器件顺序、refdes 编号、内部节点命名变了不算差异。
- 保留层次：差异标在 `.subckt` 里，不展平成一锅。
- 不确定就说不确定：同签名并联器件删掉一只、身份不可定时，给候选列表 + rc=2，**不猜一个 refdes 充数**。

## 安装

```bash
pip install .            # 需要 setuptools >= 61
# 或者零安装直接用：
PYTHONPATH=src python -m spice_diff.cli old.sp new.sp
```

要求 Python 3.9+，零运行时依赖。

## 用法

```bash
spdiff before.sp after.sp              # Markdown 报告
spdiff before.sp after.sp --json       # JSON（机读）
spdiff before.sp after.sp -o out.md    # 写文件
spdiff --version
```

### 退出码

| 码 | 含义 | CI 里怎么用 |
|---|---|---|
| 0 | 未发现结构差异 | 通过（记得那三条假阴性） |
| 1 | 发现结构差异 | 拦下，附报告 |
| 2 | 存在无法唯一判定的改动 | 拦下，要求人工指定映射 |
| 3 | 输入错误（解析失败、文件不存在） | 拦下，是脚本或文件的问题 |

## 性能

扁平网表实测（Windows / CPython 3.14，单核）：

| 器件数 | 耗时 |
|---|---|
| 1,000 | 0.17 s |
| 10,000 | 0.33 s |
| 20,000 | 0.43 s |

2 万只器件、3 万节点，0.43 秒，只报出预埋的 2 处改动，零误报。

## 支持范围

- 文件：单个 `.sp` / `.cir` / `.net` 文本文件（含 include 的网表请先自行展开）。
- 器件：`R C L D M Q X V I`。
- 指令：`.subckt .ends .model .param .global .include .end`。
- 语法：ngspice 风格 SPICE3 子集；续行 `+`、注释 `*` 与行尾 `$`、UTF-8（含 BOM）、CRLF 均可。

## 样例

`examples/` 里有五组自检用例，`tests/functional/extras/` 里另有三组加赛用例（`x1` rc=1、`x2` rc=2、`x3` rc=1），`tests/` 里有对应的期望值：

| 样例 | 期望 | 覆盖点 |
|---|---|---|
| `pair_a` | rc=0 | 行序/refdes/节点重命名/数值写法等价 |
| `pair_b` | rc=1 | 增删器件、参数变化、模型变化 |
| `pair_c` | rc=1 | `.subckt` 内的改动 |
| `pair_d` | rc=2 | 身份不可定，给候选不猜 |
| `error_bad_syntax` | rc=3 | 解析失败，stdout 为空、stderr 带行号 |

## 开发

```bash
python -m unittest discover -s tests -t .     # 63 条（2 条 expectedFailure 是已知限制的证据）
```

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 验收

- **跑什么**：上面那条 `unittest discover` 命令，在仓库根目录执行。
- **什么算过**：退出码 `0`，且输出为 `OK (expected failures=2)`；条数与本文件「开发」一节写的数字一致。
- **谁复核**：改动由**没有写它的人**亲自跑一遍后签字，作者不自签；签字人在群里贴出命令与结果，之后才允许 commit。

## 路线图

- **v0.1（当前）**：结构 diff，三条已知假阴性。
- **v0.2**：`.include` 展开、`.param` 求值、分析语句变更列为 `uncertain`；把「报等价」改成「未发现差异」的措辞。
- **v0.3**：`.subckt` 深度嵌套压测（扁平已实测到 2 万只器件）、Spectre/HSPICE 方言差异、`--fail-on` 选择器。

## 许可

MIT，见 [LICENSE](LICENSE)。版权人 XMQ。
