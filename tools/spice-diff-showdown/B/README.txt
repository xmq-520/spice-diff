spice-diff 对拍 B 版（Hermes）
================================

来源：hermes\spice-diff-impl\ ，19:20 起由 Hermes 直接写入本目录（不再需要代拷）。
自带 pyproject.toml，可独立 pip install . ；examples/ 为内置副本，与仓库 examples 同源。

一、范围
- 只含 B 版实现：src/spice_diff/{__init__,cli,core,parse}.py、tests/、examples/、pyproject.toml。
- 不含仓库其他内容，不含 tools/、tasks/。

二、跑法
  PYTHONPATH=src python -m spice_diff.cli examples/pair_b_before.sp examples/pair_b_after.sp
  python -m unittest discover -s tests -t .        # 25 条，含 2 条 expectedFailure

三、构建前提（本机实测）
- 需要 setuptools >= 61，否则 [project] 整段被忽略，装出来是 UNKNOWN-0.0.0、且没有 spdiff 命令。
- 本机系统 setuptools 是 58.1.0，直接用会踩这个坑；用 pkgs/setuptools-82.0.1 顶着装即正常。
- 另需 wheel 模块（pip 走 bdist_wheel）；本机无，可 PYTHONPATH 指到已解包的 wheel。

四、v0.1 已知限制（契约第 6 条）
以下三条是假阴性：报「无结构差异」而两份网表其实不等价。报等价不等于确认等价。
- 不解析 .param 表达式：器件值写成参数名（R1 in n1 rr）时只做字符串比较，
  仅改 .param rr=1k -> 2k 会报「无结构差异」rc=0。tests/test_edges.py 用
  expectedFailure 钉住，v0.2 修好后它会变 unexpected success。
- 不展开 .include / .inc：整行略过。两份网表各自 include 到不同子文件时同样报
  「无结构差异」rc=0，include 指向不存在的文件也不报错。调用方须先自行展开成
  单一网表再比较，v0.2 考虑内置展开。tests/test_edges.py 同样钉住。
  （19:55 dsh 按 Hermes 19:47 群内自述补记：此条此前只说了「稍后实测」，未落进本文件。）
- 分析语句（.tran/.ac/.dc/.ic 等）不参与比对。
- 数值语义：RKM 字母内嵌小数 `4k7`=`4.7k`=4700、`1R5`=1.5、`5k1`=5.1k；`1e3` 一类
  科学计数法不算 RKM。乘数按 SPICE 取值，`MEG`=兆而裸 `M`/`m` 恒为毫，故 `2M2`=2.2e-3。
- 器件子集仅 R C L D M Q X V I。

五、确定性基线（本目录实测，LF 换行）
  pair_a rc=0 9922843e73d413cf   pair_b rc=1 56a9fa9d36b1e5fd
  pair_c rc=1 be6b5498351c6e0d   pair_d rc=2 b9d9899d6bf097e1
  x1     rc=1 e345ca8be10a0a04   x2     rc=2 ddc84c87a04a27ae
  x3     rc=1 65ca4b1188723acb   error  rc=3 stdout 0 字节
说明：dsh 18:5x 记的 pair_b 指纹 d4ac390c…（CRLF）已作废，19:20 起输出统一 LF 以保跨机器字节一致。
