* error case: 语法错误 —— .subckt 没有 .ends，且 M 器件缺少节点
* 期望：解析失败，退出码 3，stderr 指明行号；不得输出任何差异
V1 in 0 DC 1
.subckt buf in out
M1 out in 0 0
