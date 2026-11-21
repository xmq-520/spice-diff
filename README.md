# spice-diff

![status](https://img.shields.io/badge/status-v0.1-brightgreen)
![license](https://img.shields.io/badge/license-MIT-blue)
![python](https://img.shields.io/badge/python-3.9%2B-blue)

**两版 SPICE 网表之间的结构变更报告。**

改版之后，两份网表到底差在哪？器件换了值、删了一个、多了一根连接、改在哪个子电路里——一条命令出报告，Markdown 给人看，JSON 给 CI 看。

> ✅ **当前状态：核心比对 `core.diff()` 已实现**（11-21 对拍 ④ 胜出版，作者 Hermes）。
> 五组样例退出码 0/1/1/2/3 全中、坏语法退出码 3 且 stdout 为空、两次运行字节级一致、
> JSON 顶层字段与本文契约一致；`tests/` 共 31 条测试全过（16 条骨架 + 15 条功能，含 3 条回归）。
>
> **已知限制（v0.1，实测确认，尚未修）**
>
> 前三条是**假阴性**：工具报「无结构差异」而两份网表其实不等价。**报等价不等于确认等价。**
>
> 1. **`.param` 值变化不检出**——器件写 `R1 in n1 rr` 时只按参数名字符串比较，
>    仅改 `.param rr=1k` → `2k` 会报「无结构差异」（rc=0）。v0.2 解析表达式后解决。
> 2. **`.include` 不展开**——整行略过。两份网表各自 include 到不同子文件时同样报「无结构差异」。
>    调用方须先自行展开成单一网表再比较；v0.2 考虑内置展开。
> 3. **分析语句（`.dc`/`.tran`/`.ac` 等）不参与比对**，改了不报。
>
> 以下三条是判定口径，非缺陷：
>
> 4. **同 refdes 同类型的器件对，只比较「两侧都出现的参数键」**（`core.py` 的 `_diff_scope`）。
>    一侧多/少一个位置型参数时，那个参数不进比较，**不会报变化**。等值写法已归一化
>    （`4k7` = `4.7e3` = `4700`），但「键集合不同」这一类仍会漏判。
> 5. `2milli` 被按 `mil` 解析成 `5.08e-5`（应为 `2e-3`）；裸 `M` 按「毫」取 `1e-3`、
>    `2M2` = `2.2e-3`（与 NGSPICE 把裸 `M` 当 `mega` 不同）。此口径已写进契约第 2 条。v0.2 复议。
> 6. 顶层未声明 `.global` 的网络视为内部节点，**整体改名不算改动**（契约第 2 条要求）。
>
> 前三条各有测试守着，以 `expectedFailure` 形式固化在 `tests/`：修好那天它会自己变红提醒，
> 证据不删。
>
> 下面「设计要点 / 契约 / 样例」即 v0.1 契约，已按此实现。

## 它不是 LVS

| | LVS 类工具 | spice-diff |
|---|---|---|
| 目的 | 判定两份网表是否等价 | 报告两版之间**改了什么** |
| 层次 | 展平到晶体管级 | **保留 `.subckt` 层次**，指出具体子电路 |
| 输出 | MATCH / MISMATCH | 变更清单 + Markdown 报告，可贴 PR |
| 不确定时 | 判为不匹配 | 报 `uncertain` + 候选映射，**不猜** |
| 典型用法 | 版图 vs 原理图 | v1 vs v2、改版审阅、CI 门禁 |

## 设计要点

- **与书写形式无关**：行序、器件顺序、refdes 编号、内部节点命名、数值写法（`1k` / `1000` / `1e3`、`1MEG` / `1e6`）改变，都不产生差异。
- **保留层次**：改动报在 `buf/R1`，而不是摊平成一堆顶层晶体管。
- **不猜**：同签名器件身份无法唯一确定时（例如两个相同的并联电阻少了一个），报 `refdes: null` + 候选列表，退出码 2。
- **确定性**：同一对输入跑两次，输出字节级一致。不写时间戳、不写绝对路径、不写主机名。
- **纯标准库**：Python 3.9+，无第三方依赖。

## 安装

```bash
git clone https://github.com/xmq-520/spice-diff.git
cd spice-diff
pip install .
```

两个已知坑：

- 本机 pip 缓存目录权限异常时，先设 `PIP_NO_CACHE_DIR=1`（PowerShell：`$env:PIP_NO_CACHE_DIR='1'`）。
- setuptools 过老（< 61）的机器上，先 `pip install -U setuptools wheel` 再装。

## 用法

```bash
spdiff before.sp after.sp                  # Markdown 到 stdout
spdiff before.sp after.sp --json           # JSON 到 stdout
spdiff before.sp after.sp --format md -o report.md
```

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 无结构差异 |
| 1 | 有结构差异 |
| 2 | 存在无法完全判定的差异（`uncertain`） |
| 3 | 输入错误（解析失败、文件不存在） |

## 契约（v0.1）

### 归一化
- **续行**：`+` 与上一行拼接后再解析；注释 `*`、行尾 `$` 先剥离。
- **节点**：`0` 恒为地；`.global` 声明的网络固定身份；其余内部节点按拓扑位置规范化，不按出现顺序编号。
- **数值**：`1k` / `1K` / `1000` / `1e3` 相等；`1MEG` / `1meg` / `1e6` 相等；`1m` 一律是毫（`1e-3`）。
- **参数**：键名大小写不敏感；只比双方都出现的参数。
- **`.model`**：单独报 `model_changed`；只比括号内双方都出现的参数。
- **层次路径**：`/` 连接，顶层记 `top`；`.subckt buf` 内的 R1 是 `buf/R1`，嵌套为 `buf/X1/R2`。X 实例本身的增删记在父层。

### 对齐
- 签名分组，组内一对一直配。
- 多对多做子图匹配；不唯一则 `uncertain` + 候选，不任选。
- 数量可定、身份不可定：报 `device_added` / `device_removed`，`refdes` 为 `null`，附 `candidates`，退出码 2。

### JSON 结构（冻结）

```json
{
  "tool": "spice-diff",
  "version": "0.1.0",
  "summary": {
    "device_added": 0, "device_removed": 0, "param_changed": 1,
    "connection_changed": 0, "model_changed": 0, "uncertain": 0
  },
  "changes": [
    {"kind": "param_changed", "scope": "top", "refdes": "R2",
     "param": "value", "before": "2k", "after": "3k"}
  ],
  "exit_code": 1
}
```

`changes` 按 `(scope, refdes, kind)` 升序。v0.1 不加字段。

## 样例

`examples/` 下五组，含黄金期望输出（13 个文件，已入库）：

| 用例 | 验什么 | 期望 |
|---|---|---|
| `pair_a` | 重排行序、换 refdes、改内部节点名、换数值写法 | 零差异，退出码 0 |
| `pair_b` | 阻值变、电容删、二极管加、model 参数变 | 见 `expected_b.md` |
| `pair_c` | 改动藏在 `.subckt` 内部 | `scope: buf`，不展平 |
| `pair_d` | 同签名并联电阻少一个 | `refdes: null` + 候选，退出码 2 |
| `error_bad_syntax` | 语法错误 | 退出码 3，stdout 为空，stderr 带行号 |

`error_bad_syntax` 的报错行号是 **`:5:`**（`M1` 在第 5 行）。

## 测试

```bash
python -m unittest discover -s tests/unit -t .        # 16 条：打包/CLI 面/退出码/3.9 语法兜底
python -m unittest discover -s tests/functional -t .  # 15 条：子进程真跑，含 x1-x3 回归
```

`tests/functional/extras/` 是 11-21 对拍后封存的三对回归样例（x1 等值写法 + 子电路内改动、
x2 同签名删一、x3 `.global` 锚点），带 SHA256，不许改动。

## 路线图

- **v0.1**：解析 + 归一化 + 对齐 + Markdown/JSON 双输出（已交付，见文首已知限制）
- **v0.2**：`.include` 展开、更多器件类型、补齐「键集合不同」的比较（已知限制 1）
- **v0.3**：GitHub Action 封装，PR 自动贴变更摘要

## 许可

MIT © 2026 XMQ
