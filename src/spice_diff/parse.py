"""SPICE 网表解析（v0.1 契约：续行、注释、层次、器件子集）。

只做解析与结构化，不做判定。出错一律抛 ParseError，带文件名与行号，
绝不"尽力而为"地跳过坏行——那会把语法错误报成器件删除。
"""

from __future__ import annotations

from typing import Dict, List, Optional


class ParseError(Exception):
    def __init__(self, fname: str, line: int, ref: str, msg: str) -> None:
        self.fname = fname
        self.line = line
        self.ref = ref
        self.msg = msg
        super().__init__("%s:%d: <%s> %s" % (fname, line, ref, msg))


class Device:
    __slots__ = ("ref", "typ", "nodes", "model", "params", "raw", "line")

    def __init__(self, ref, typ, nodes, model, params, raw, line):
        self.ref = ref
        self.typ = typ
        self.nodes = nodes
        self.model = model
        self.params = params      # 键小写，值原始字符串（保序）
        self.raw = raw
        self.line = line

    def __repr__(self):
        return "<Device %s %s>" % (self.typ, self.ref)


class Subckt:
    __slots__ = ("name", "ports", "devices", "line")

    def __init__(self, name, ports, line):
        self.name = name
        self.ports = ports
        self.devices: List[Device] = []
        self.line = line


class Model:
    __slots__ = ("name", "mtype", "params", "line")

    def __init__(self, name, mtype, params, line):
        self.name = name
        self.mtype = mtype
        self.params = params
        self.line = line

    def text(self):
        if not self.params:
            return self.mtype
        body = " ".join("%s=%s" % (k.upper(), v) for k, v in self.params.items())
        return "%s(%s)" % (self.mtype, body)


class Circuit:
    __slots__ = ("top", "subckts", "models", "globals")

    def __init__(self):
        self.top: List[Device] = []
        self.subckts: Dict[str, Subckt] = {}   # 键小写
        self.models: Dict[str, Model] = {}     # 键小写
        self.globals = set()

    def scopes(self):
        """返回 (scope_key, 展示名, 端口列表, 器件列表)——顶层 key 为 'top'。"""
        out = [("top", "top", [], self.top)]
        for k in sorted(self.subckts):
            s = self.subckts[k]
            out.append((k, s.name, s.ports, s.devices))
        return out


# 每种器件的最少节点数（不含 model / value 之外的合法写法）
_MIN_NODES = {
    "R": 2, "C": 2, "L": 2, "V": 2, "I": 2,
    "D": 2, "M": 4, "Q": 3, "J": 3,
    "E": 4, "F": 4, "G": 4, "H": 4,
}


def _strip_inline_comment(s: str) -> str:
    i = s.find("$")
    if i >= 0:
        s = s[:i]
    return s


def _logical_lines(text: str):
    """合并续行；产出 (起始行号, 逻辑行)。注释行与空行跳过。"""
    pending = None
    start = 0
    for idx, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r\n")
        s = line.strip()
        if not s:
            continue
        if s.startswith("*"):
            continue
        s = _strip_inline_comment(s).strip()
        if not s:
            continue
        if s.startswith("+"):
            if pending is None:
                raise ParseError("<netlist>", idx, "+", "续行前面没有可续的行")
            pending = pending + " " + s[1:].strip()
            continue
        if pending is not None:
            yield start, pending
        pending = s
        start = idx
    if pending is not None:
        yield start, pending


def _split_params(tokens):
    """尾部 key=value 归参数，返回 (其余 token, 有序参数 dict)。"""
    head, params = [], {}
    for t in tokens:
        if "=" in t and not t.startswith("="):
            k, v = t.split("=", 1)
            if k:
                params[k.lower()] = v
                continue
        head.append(t)
    return head, params


def _device(tokens, line, fname):
    ref = tokens[0]
    typ = ref[0].upper()
    rest = tokens[1:]
    model = None

    if typ == "X":
        head, params = _split_params(rest)
        if len(head) < 2:
            raise ParseError(fname, line, ref, "子电路实例缺少节点或子电路名")
        model = head[-1]
        nodes = head[:-1]
        # SPICE 允许数字节点名（提取工具常直接输出 1 2 3），不再判非法；
        # 尾部 key=value 已由 _split_params 归入参数，剩下的都当节点。
        return Device(ref, typ, nodes, model, params, " ".join(tokens), line)

    if typ in ("R", "C", "L", "V", "I"):
        head, params = _split_params(rest)
        # V/I 允许 DC/AC 关键字与数值，其余类型第 3 个 token 是值
        if typ in ("V", "I"):
            nums = [t for t in head]
            if len(nums) < 3:
                raise ParseError(fname, line, ref, "节点数不足")
            # 形如 V1 in 0 DC 1 / V1 in 0 1
            keep = [nums[0], nums[1]]
            tail = " ".join(nums[2:])
            if tail:
                params.setdefault("value", tail.split()[0] if len(tail.split()) == 1 else tail)
            return Device(ref, typ, keep, model, params, " ".join(tokens), line)
        if len(head) < 3:
            raise ParseError(fname, line, ref, "节点数不足")
        params.setdefault("value", head[2])
        return Device(ref, typ, head[:2], model, params, " ".join(tokens), line)

    if typ == "D":
        head, params = _split_params(rest)
        if len(head) < 3:
            raise ParseError(fname, line, ref, "节点数不足")
        return Device(ref, typ, head[:2], head[2], params, " ".join(tokens), line)

    if typ == "M":
        head, params = _split_params(rest)
        if len(head) < 5:
            raise ParseError(fname, line, ref, "节点数不足")
        return Device(ref, typ, head[:4], head[4], params, " ".join(tokens), line)

    if typ in ("Q", "J"):
        head, params = _split_params(rest)
        if len(head) < 4:
            raise ParseError(fname, line, ref, "节点数不足")
        nodes = head[:4] if len(head) >= 5 else head[:3]
        return Device(ref, typ, nodes, head[len(nodes)], params, " ".join(tokens), line)

    if typ in ("E", "F", "G", "H"):
        head, params = _split_params(rest)
        if len(head) < 5:
            raise ParseError(fname, line, ref, "节点数不足")
        params.setdefault("value", head[4])
        return Device(ref, typ, head[:4], model, params, " ".join(tokens), line)

    # 未知器件：保留，按 名称 + 节点 处理，宁可比不上也不静默丢弃
    head, params = _split_params(rest)
    if len(head) < _MIN_NODES.get(typ, 1):
        raise ParseError(fname, line, ref, "节点数不足")
    return Device(ref, typ, head, model, params, " ".join(tokens), line)


def _looks_numeric(tok: str) -> bool:
    if not tok:
        return False
    c = tok[0]
    return c.isdigit() or c in "+-."


def parse_text(text: str, fname: str = "<netlist>") -> Circuit:
    circ = Circuit()
    cur: Optional[Subckt] = None
    last_line = 0
    in_control = False
    for line, logical in _logical_lines(text):
        last_line = line
        tokens = logical.split()
        if not tokens:
            continue
        head = tokens[0].lower()

        # .control ... .endc 里是解释器脚本（set/run/meas/dowhile…），不是网表
        if head == ".control":
            in_control = True
            continue
        if head == ".endc":
            in_control = False
            continue
        if in_control:
            continue

        # SPICE 约定：第一行是标题行。但不少工具导出的网表没有标题、首行就是器件，
        # 所以只在「首行根本解析不成器件」时才当标题跳过，绝不静默吞掉真器件。
        if line == 1:
            try:
                _device(tokens, line, fname)
            except ParseError:
                continue

        if head == ".subckt":
            if cur is not None:
                raise ParseError(fname, line, tokens[0], "嵌套 .subckt 不允许")
            if len(tokens) < 2:
                raise ParseError(fname, line, ".subckt", "缺少子电路名")
            name = tokens[1]
            ports = [t for t in tokens[2:] if "=" not in t]
            cur = Subckt(name, [p.lower() for p in ports], line)
            circ.subckts[name.lower()] = cur
            continue

        if head == ".ends":
            if cur is None:
                raise ParseError(fname, line, ".ends", "没有对应的 .subckt")
            cur = None
            continue

        if head == ".model":
            if len(tokens) < 3:
                raise ParseError(fname, line, ".model", "缺少模型名或类型")
            name = tokens[1]
            body = " ".join(tokens[2:])
            params = {}
            mtype = body
            if "(" in body:
                mtype = body.split("(", 1)[0].strip()
                inner = body.split("(", 1)[1]
                inner = inner.rsplit(")", 1)[0]
                for kv in inner.replace(",", " ").split():
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        params[k.lower()] = v
            circ.models[name.lower()] = Model(name, mtype, params, line)
            continue

        if head == ".global":
            for n in tokens[1:]:
                circ.globals.add(n.lower())
            continue

        if head == ".end":
            break

        if head.startswith("."):
            continue  # .param / .option / .include / .temp 等在 v0.1 不参与比对

        dev = _device(tokens, line, fname)
        dev.ref = dev.ref
        dev.nodes = [n.lower() for n in dev.nodes]
        if cur is None:
            circ.top.append(dev)
        else:
            cur.devices.append(dev)

    if cur is not None:
        raise ParseError(fname, last_line or 1, ".subckt " + cur.name, "缺少 .ends")
    return circ


def parse_file(path: str) -> Circuit:
    try:
        # utf-8-sig：别人存盘常带 BOM，BOM 不能变成器件名的一部分
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            text = fh.read()
    except FileNotFoundError:
        raise ParseError(path, 0, "file", "文件不存在")
    except OSError as exc:
        raise ParseError(path, 0, "file", "无法读取: %s" % exc)
    return parse_text(text, path)
