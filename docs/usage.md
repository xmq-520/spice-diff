# 用法详解

## 基本调用

```bash
spdiff BEFORE.sp AFTER.sp
```

参数顺序即「旧 → 新」。报告里的「变更前 / 变更后」按这个方向填。

## 输出格式

默认 Markdown。`--json` 输出机读结构（v0.1 冻结，不加字段）：

```json
{
  "tool": "spice-diff",
  "version": "0.1.0",
  "summary": {
    "device_added": 1,
    "device_removed": 1,
    "param_changed": 1,
    "connection_changed": 0,
    "model_changed": 1,
    "uncertain": 0
  },
  "changes": [
    {
      "kind": "param_changed",
      "scope": "top",
      "refdes": "R2",
      "before": "2k",
      "after": "3k",
      "signature_before": "R2 n1 0 2k",
      "signature_after": "R2 n1 0 3k"
    }
  ]
}
```

`changes` 按 `(scope, refdes, kind)` 升序，保证字节级稳定。

## 差异分类

| kind | 含义 | 例子 |
|---|---|---|
| `device_removed` | 器件没了 | 删掉 `C1 n1 0 10p` |
| `device_added` | 器件多了 | 新增 `D2 0 out DMOD` |
| `param_changed` | 值变了 | `R2 2k` → `3k` |
| `connection_changed` | 接法变了 | `R1 in n1` → `R1 out n1` |
| `model_changed` | `.model` 内容变了 | `N=1` → `N=1.05` |
| `uncertain` | 身份无法唯一确定 | 三只同签名 `1k` 删掉一只 |

`uncertain` 时 `refdes` 为 `null`，另给 `candidates` 数组，退出码 2。
**填一个具体 refdes 就算猜，属实现缺陷。**

## 在 CI 里用

```bash
spdiff base.sp head.sp --json > diff.json || rc=$?
case "${rc:-0}" in
  0) echo "无结构差异" ;;
  1) echo "有改动，请人工确认"; exit 1 ;;
  2) echo "身份不确定，需人工指定"; exit 1 ;;
  3) echo "输入错误"; exit 1 ;;
esac
```

注意 rc=0 只代表「没有找到结构差异」，不代表等价，见 [limitations.md](limitations.md)。

## 数值写法

| 写法 | 含义 |
|---|---|
| `4k7` / `4.7k` / `4700` / `4.7e3` | 全部相等 |
| `1R5` | 1.5 |
| `5k1` | 5.1k |
| `2M2` | 2.2 毫（`M` 恒为 milli） |
| `2.2MEG` / `2.2e6` | 2.2 兆 |

要写兆请用 `MEG` 或科学计数法，不要用 `M`。

## 退出码速查

| 码 | 含义 |
|---|---|
| 0 | 未发现结构差异 |
| 1 | 发现结构差异 |
| 2 | 存在无法唯一判定的改动 |
| 3 | 输入错误（解析失败 / 文件不存在 / 读不出） |

解析失败时 **stdout 一个字节都不出**，错误只走 stderr，格式 `文件名:行号: <refdes> 消息`。
这是刻意的：CI 里拿 stdout 当报告用，半截报告比没有报告更危险。
