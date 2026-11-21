# spice-diff

![status](https://img.shields.io/badge/status-WIP-orange)
![license](https://img.shields.io/badge/license-MIT-blue)
![python](https://img.shields.io/badge/python-3.9%2B-blue)

**两版 SPICE 网表之间的结构变更报告。**

改版之后，两份网表到底差在哪？器件换了值、删了一个、多了一根连接、改在哪个子电路里——一条命令出报告，Markdown 给人看，JSON 给 CI 看。

> ⚠️ **当前状态：开发中（骨架）。** 已就位并实测可用：打包安装、命令行、契约定义、单元自检。
> **尚未实现：核心比对 `core.diff()`。** 现在拿两份网表去比，`spdiff` 会打印
> `core not implemented yet` 并返回退出码 3 —— 这是占位行为，不是比对结果。
> 下面的「设计要点 / 契约 / 样例」是**已冻结的目标契约**，请当作规格读，不要当作已交付的功能。
> 实现落地后会以独立 commit 推上来，届时本节状态同步更新。

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
| 3 | 输入错误（解析失败、文件不存在、核心未实现） |

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
| `error_bad_syntax` | 语法错误 | 退出码 3，不输出差异 |

## 路线图

- **v0.1**：解析 + 归一化 + 对齐 + Markdown/JSON 双输出（进行中）
- **v0.2**：`.include` 展开、更多器件类型
- **v0.3**：GitHub Action 封装，PR 自动贴变更摘要

## 许可

MIT © 2026 XMQ
