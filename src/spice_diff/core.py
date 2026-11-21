"""归一化 + 对齐 + diff + 报告（v0.1 契约实现）。

判定规则（与 README/ACCEPTANCE 一致）：
- refdes 相同且类型相同 → 同一器件；否则按「类型 + 节点数 + 参数」唯一匹配（重编号/重命名）。
- 节点：`0`、子电路端口、`.global` 是锚点，必须同名；其余节点允许改名，靠配对推导映射，
  映射冲突才判 connection_changed——因此"整体改名"不产生假阳性。
- 参数、模型参数：只比双方都出现的键。
- 同签名器件数量变化而身份不唯一 → refdes=null + candidates，退出码 2；唯一 → 直接点名，退出码 1。
"""

from __future__ import annotations

import json
import math
import re
from typing import Dict, List, Optional, Tuple

from .parse import Circuit, Device, Model, Subckt

EXIT_NO_DIFF = 0
EXIT_DIFF = 1
EXIT_UNCERTAIN = 2
EXIT_INPUT_ERROR = 3

_SUFFIX = {"t": 1e12, "g": 1e9, "meg": 1e6, "k": 1e3, "m": 1e-3,
           "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15, "r": 1.0}

_NUM_RE = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)([a-zA-Z]*)$")
# RKM / 字母内嵌小数：4k7 = 4.7k、1R5 = 1.5、2M2 = 2.2M
_RKM_RE = re.compile(r"^([+-]?)(\d*)([A-Za-z]+)(\d+)$")


def _multiplier(suf: str) -> float:
    if not suf:
        return 1.0
    if suf.startswith("meg"):
        return 1e6
    if suf.startswith("mil"):
        return 25.4e-6
    return _SUFFIX.get(suf[0], 1.0)


def to_number(tok: str) -> Optional[float]:
    """SPICE 数值：1k / 1000 / 1e3 相等；1MEG / 1e6 相等；1m 一律毫；4k7 = 4.7e3 = 4700。"""
    if tok is None:
        return None
    s = tok.strip()
    m = _RKM_RE.match(s)
    if m and not m.group(3).lower().startswith("e"):  # 1e3 不是 RKM
        sign, ip, suf, fp = m.groups()
        return float("%s%s.%s" % (sign, ip or "0", fp)) * _multiplier(suf.lower())
    m = _NUM_RE.match(s)
    if not m:
        return None
    val = float(m.group(1))
    suf = m.group(2).lower()
    return val * _multiplier(suf)


def fmt_num(v: float) -> str:
    if v == 0:
        return "0"
    av = abs(v)
    if av >= 1e3 or av < 1e-3:
        exp = int(math.floor(math.log10(av)))
        mant = v / (10.0 ** exp)
        ms = "%.6g" % mant
        if ms in ("10", "10.0"):
            return "1e%d" % (exp + 1)
        return "%se%d" % (ms, exp)
    return "%.6g" % v


def _same(a: str, b: str) -> bool:
    na, nb = to_number(a), to_number(b)
    if na is not None and nb is not None:
        if na == nb:
            return True
        scale = max(abs(na), abs(nb), 1e-30)
        return abs(na - nb) <= 1e-9 * scale
    return a.strip().lower() == b.strip().lower()


def _disp(tok: str) -> str:
    n = to_number(tok)
    if n is None:
        return tok
    return "%s (%s)" % (tok, fmt_num(n))


class Change:
    __slots__ = ("kind", "scope", "refdes", "data", "ambiguous")

    def __init__(self, kind, scope, refdes, ambiguous=False, **data):
        self.kind = kind
        self.scope = scope
        self.refdes = refdes
        self.ambiguous = ambiguous
        self.data = data

    def sort_key(self):
        return (self.scope, self.refdes or "~", self.kind, json.dumps(self.data, sort_keys=True))

    def to_json(self):
        out = {"kind": self.kind, "scope": self.scope, "refdes": self.refdes}
        inner = {k: v for k, v in self.data.items() if not k.startswith("_")}
        out.update(inner)
        return out


class Result:
    def __init__(self, changes: List[Change]):
        self.changes = sorted(changes, key=lambda c: c.sort_key())

    def count(self, kind):
        return sum(1 for c in self.changes if c.kind == kind)

    @property
    def summary(self):
        return {
            "device_added": self.count("device_added"),
            "device_removed": self.count("device_removed"),
            "param_changed": self.count("param_changed"),
            "connection_changed": self.count("connection_changed"),
            "model_changed": self.count("model_changed"),
            "uncertain": sum(1 for c in self.changes if c.ambiguous),
        }

    @property
    def exit_code(self):
        if any(c.ambiguous for c in self.changes):
            return EXIT_UNCERTAIN
        if self.changes:
            return EXIT_DIFF
        return EXIT_NO_DIFF


# ---------------------------------------------------------------- 签名与配对

def _sig_strict(d: Device):
    return (d.typ, tuple(d.nodes), tuple(sorted(d.params.items())))


def _sig_loose(d: Device):
    return (d.typ, len(d.nodes), tuple(sorted(d.params.items())))


def _by_ref(devs):
    out = {}
    for d in devs:
        out.setdefault(d.ref.upper(), []).append(d)
    return out


def _anchor(net, ports, globals_):
    return net == "0" or net in ports or net in globals_


def _diff_scope(scope, ports_b, devs_b, ports_a, devs_a, globals_):
    changes: List[Change] = []
    pairs: List[Tuple[Device, Device]] = []
    used_b, used_a = set(), set()

    # 0) 完全相同的实例先一对一配掉。
    #    同一 refdes 在一个文件里出现多次（实例化不同子电路，如 xrcv->bjtdrvr / xrcv->dioload）
    #    时，按 refdes 配对会退化成「增删各一条」，导致**同一份文件跟自己比也报差异**。
    #    先配字面完全相同的，这类文件自然归零；剩下的才按 refdes / 签名走。
    def _exact_key(d):
        return (d.ref.upper(), d.typ, d.model, tuple(d.nodes), tuple(sorted(d.params.items())))

    exact_b, exact_a = {}, {}
    for d in devs_b:
        exact_b.setdefault(_exact_key(d), []).append(d)
    for d in devs_a:
        exact_a.setdefault(_exact_key(d), []).append(d)
    for key in set(exact_b) & set(exact_a):
        for db, da in zip(exact_b[key], exact_a[key]):
            pairs.append((db, da))
            used_b.add(id(db))
            used_a.add(id(da))

    rb, ra = _by_ref(devs_b), _by_ref(devs_a)

    for ref in sorted(set(rb) & set(ra)):
        if len(rb[ref]) == 1 and len(ra[ref]) == 1 and rb[ref][0].typ == ra[ref][0].typ:
            if id(rb[ref][0]) in used_b or id(ra[ref][0]) in used_a:
                continue
            pairs.append((rb[ref][0], ra[ref][0]))
            used_b.add(id(rb[ref][0]))
            used_a.add(id(ra[ref][0]))

    left_b = [d for d in devs_b if id(d) not in used_b]
    left_a = [d for d in devs_a if id(d) not in used_a]

    # 重编号/重命名：松散签名唯一则配成一对
    gb, ga = {}, {}
    for d in left_b:
        gb.setdefault(_sig_loose(d), []).append(d)
    for d in left_a:
        ga.setdefault(_sig_loose(d), []).append(d)
    for key in sorted(set(gb) & set(ga), key=repr):
        if len(gb[key]) == 1 and len(ga[key]) == 1:
            pairs.append((gb[key][0], ga[key][0]))
            used_b.add(id(gb[key][0]))
            used_a.add(id(ga[key][0]))

    left_b = [d for d in devs_b if id(d) not in used_b]
    left_a = [d for d in devs_a if id(d) not in used_a]

    # 剩余：唯一签名 → 点名；多候选 → uncertain
    for d in left_b:
        cands = sorted({x.ref for x in devs_b if _sig_strict(x) == _sig_strict(d)} |
                       {x.ref for x in left_b if _sig_loose(x) == _sig_loose(d)})
        if len(cands) <= 1:
            changes.append(Change("device_removed", scope, d.ref, before=d.raw, after=None))
        else:
            changes.append(Change("device_removed", scope, None, ambiguous=True,
                                  before=d.raw, after=None, candidates=cands))
    for d in left_a:
        cands = sorted({x.ref for x in devs_a if _sig_strict(x) == _sig_strict(d)} |
                       {x.ref for x in left_a if _sig_loose(x) == _sig_loose(d)})
        if len(cands) <= 1:
            changes.append(Change("device_added", scope, d.ref, before=None, after=d.raw))
        else:
            changes.append(Change("device_added", scope, None, ambiguous=True,
                                  before=None, after=d.raw, candidates=cands))

    # 节点映射（锚点必须同名；内部节点允许改名，冲突即连接变化）
    fwd, rev = {}, {}
    bad_pairs = set()
    for i, (db, da) in enumerate(pairs):
        if len(db.nodes) != len(da.nodes):
            bad_pairs.add(i)
            continue
        for nb, na in zip(db.nodes, da.nodes):
            if _anchor(nb, ports_b, globals_) or _anchor(na, ports_a, globals_):
                if nb != na:
                    bad_pairs.add(i)
                continue
            if nb in fwd and fwd[nb] != na:
                bad_pairs.add(i)
            if na in rev and rev[na] != nb:
                bad_pairs.add(i)
            fwd.setdefault(nb, na)
            rev.setdefault(na, nb)

    for i, (db, da) in enumerate(pairs):
        if i in bad_pairs:
            changes.append(Change("connection_changed", scope, da.ref,
                                  before=db.raw, after=da.raw,
                                  nodes_before=list(db.nodes), nodes_after=list(da.nodes)))
        for k in sorted(set(db.params) & set(da.params)):
            if not _same(db.params[k], da.params[k]):
                changes.append(Change("param_changed", scope, da.ref, param=k,
                                      before=db.params[k], after=da.params[k]))
        if db.model and da.model and db.model.strip().lower() != da.model.strip().lower():
            changes.append(Change("param_changed", scope, da.ref, param="model",
                                  before=db.model, after=da.model))

    return changes


def _diff_models(mb: Dict[str, Model], ma: Dict[str, Model], scope="top"):
    changes = []
    for name in sorted(set(mb) & set(ma)):
        m1, m2 = mb[name], ma[name]
        for k in sorted(set(m1.params) & set(m2.params)):
            if not _same(m1.params[k], m2.params[k]):
                changes.append(Change("model_changed", scope, m2.name, param=k,
                                      before=m1.params[k], after=m2.params[k],
                                      _model_before=m1.text(), _model_after=m2.text()))
    return changes


def diff(before: Circuit, after: Circuit) -> Result:
    changes: List[Change] = []
    sb = {k: (disp, ports, devs) for k, disp, ports, devs in before.scopes()}
    sa = {k: (disp, ports, devs) for k, disp, ports, devs in after.scopes()}

    for key in sorted(set(sb) | set(sa)):
        if key not in sa:
            disp, ports, devs = sb[key]
            for d in devs:
                changes.append(Change("device_removed", key, d.ref, before=d.raw, after=None))
            continue
        if key not in sb:
            disp, ports, devs = sa[key]
            for d in devs:
                changes.append(Change("device_added", key, d.ref, before=None, after=d.raw))
            continue
        _, pb, db_ = sb[key]
        _, pa, da_ = sa[key]
        changes.extend(_diff_scope(key, pb, db_, pa, da_, before.globals | after.globals))

    changes.extend(_diff_models(before.models, after.models))

    # uncertain 条目统一记在 summary 里
    return Result(changes)


# ---------------------------------------------------------------- 渲染

_KIND_ORDER = ("param_changed", "connection_changed", "device_removed",
               "device_added", "model_changed")


def _scope_disp(scope):
    return "顶层" if scope == "top" else "`%s`" % scope


def _module_table(result: Result) -> List[str]:
    """按模块（.subckt 作用域）汇总变更数——大面积改动时先看这张表，再看明细。"""
    order = ["device_added", "device_removed", "param_changed", "connection_changed", "model_changed"]
    per: Dict[str, Dict[str, int]] = {}
    for c in result.changes:
        slot = per.setdefault(c.scope, {k: 0 for k in order})
        if c.kind in slot:
            slot[c.kind] += 1
    if not per:
        return []
    scopes = sorted(per, key=lambda s: (s != "top", s))

    def cell(slot, kind):
        return str(slot[kind]) if slot[kind] else "—"

    lines = ["## 按模块汇总", "",
             "| 模块 | 新增 | 删除 | 参数 | 连接 | 模型 | 合计 |",
             "|---|---|---|---|---|---|---|"]
    for s in scopes:
        slot = per[s]
        lines.append("| %s | %s | %s | %s | %s | %s | %d |"
                     % (_scope_disp(s), cell(slot, "device_added"), cell(slot, "device_removed"),
                        cell(slot, "param_changed"), cell(slot, "connection_changed"),
                        cell(slot, "model_changed"), sum(slot.values())))
    return lines


_RISKY_PASSIVE = ("R", "C", "L")


def _risk_notes(result: Result) -> List[str]:
    """风险提示：只做启发式分诊，不做判定，也不替代人工复核。"""
    s = result.summary
    notes: List[str] = []
    if s["device_removed"]:
        names = [c.refdes for c in result.changes if c.kind == "device_removed" and c.refdes][:6]
        notes.append("**删除器件 %d 个**%s：先确认不是被搬进子电路；删除常留下悬空节点或未更新的激励。"
                     % (s["device_removed"], "（%s）" % "、".join(names) if names else ""))
    if s["connection_changed"]:
        notes.append("**连接变化 %d 处**：改线最容易造成短路、极性反接或漏接，建议优先人工复核。"
                     % s["connection_changed"])
    pas = [c.refdes for c in result.changes
           if c.kind in ("param_changed",) and c.refdes
           and c.refdes[0].upper() in _RISKY_PASSIVE]
    if pas:
        notes.append("**无源件取值变化 %d 处**（%s）：影响时间常数、阻抗与偏置点，"
                     "建议与仿真结果对照，不要只看行数。"
                     % (len(pas), "、".join(pas[:8])))
    if s["model_changed"]:
        names = [c.refdes for c in result.changes if c.kind == "model_changed" and c.refdes][:6]
        notes.append("**模型参数变化 %d 处**%s：影响所有引用该模型的器件，影响面大于改动行数。"
                     % (s["model_changed"], "（%s）" % "、".join(names) if names else ""))
    if s["uncertain"]:
        notes.append("**%d 条无法判定身份**：数量可定、身份不可定，不能据此放行。" % s["uncertain"])
    if not notes:
        notes.append("只有新增器件等低风险改动，仍建议对改动所在模块跑一次仿真确认。")
    return ["## 风险提示", "",
            "以下为启发式分诊，不是判定结论："] + ["- " + n for n in notes]



def _base(path):
    """输出里只留文件名——不写绝对路径，保证同一对输入在任何机器上字节一致。"""
    return str(path).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]


def render_markdown(result: Result, before_name="before", after_name="after",
                    explain: bool = False) -> str:
    s = result.summary
    lines = ["# spice-diff：%s → %s" % (_base(before_name), _base(after_name)), ""]
    if not result.changes:
        lines += ["无结构差异。", "", "退出码 0（未发现结构差异；这不等于两份网表等价，见 docs/limitations.md）。", ""]
        return "\n".join(lines)

    lines += ["## 变更摘要", "",
              "- 器件新增：%d　器件删除：%d　参数变化：%d　连接变化：%d　模型变化：%d　不确定：%d"
              % (s["device_added"], s["device_removed"], s["param_changed"],
                 s["connection_changed"], s["model_changed"], s["uncertain"]),
              ""]
    if explain:
        mod = _module_table(result)
        if mod:
            lines += mod + [""]
        lines += _risk_notes(result) + [""]
    lines += ["## 明细", "",
              "| 类别 | 位置 | 器件 | 变更前 | 变更后 |", "|---|---|---|---|---|"]

    for c in result.changes:
        ref = "（未知）" if c.ambiguous else (c.refdes or "—")
        if c.kind == "param_changed":
            row = (c.kind, _scope_disp(c.scope), ref,
                   _disp(c.data["before"]), _disp(c.data["after"]))
        elif c.kind == "model_changed":
            row = (c.kind, _scope_disp(c.scope), ref,
                   c.data.get("_model_before", c.data["before"]),
                   c.data.get("_model_after", c.data["after"]))
        else:
            row = (c.kind, _scope_disp(c.scope), ref,
                   c.data.get("before") or "—", c.data.get("after") or "—")
        lines.append("| %s | %s | %s | %s | %s |" % row)

    unc = [c for c in result.changes if c.ambiguous]
    if unc:
        lines += ["", "## 不确定（需人工判定）", ""]
        for c in unc:
            cands = c.data["candidates"]
            if len(cands) == 1:
                why = "唯一可能是 `%s`，但差一个实例也可能来自别处，无法证明，故不猜。" % cands[0]
            else:
                why = "候选有 %d 个（`%s`），多选一即等于猜，不猜。" % (len(cands), "`, `".join(cands))
            lines.append("- %s：%s 的实例数量对不上，数量可定、身份不可定。%s"
                         % (c.kind, _scope_disp(c.scope), why))
        lines += ["", "> 不确定条目不参与 rc=0 判定；一条不确定即退出码 2。"]

    if s["uncertain"]:
        lines += ["", "退出码 2（存在无法完全判定的差异）。", ""]
    else:
        lines += ["", "退出码 1（存在结构差异）。", ""]
    return "\n".join(lines)


def render_json(result: Result, before_name="before", after_name="after") -> str:
    payload = {
        "tool": "spice-diff",
        "version": "0.1.0",
        "summary": result.summary,
        "changes": [c.to_json() for c in result.changes],
        "exit_code": result.exit_code,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
