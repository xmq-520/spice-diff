# 期望输出：pair_d（身份不可判定）

签名类 `R(in,out,1k)` 由 2 个降为 1 个：**数量变了可以确定，身份不能确定。**

## 期望（严格）

```json
{"kind":"device_removed","scope":"top","refdes":null,
 "candidates":[{"refdes":"R1"},{"refdes":"R2"}]}
```

## 断言要点
1. `refdes` 必须是 `null`，**不许**随便填 R1 或 R2 —— 填任何一个即为「猜」，判败。
2. `candidates` 两个都在，顺序按 refdes 升序。
3. 退出码 **2**（存在无法完全判定的差异），不是 1。
4. 反过来（after 里多一个同签名器件）同样处理，`kind` 为 `device_added`。
