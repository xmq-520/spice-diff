* pair_c: 层次定位用例 —— 改动藏在子电路内部
* 期望：差异报在 buf/R1，而不是展开成一堆顶层器件
V1 in 0 DC 1
.subckt buf in out
R1 out 0 1k
M1 out in 0 0 NMOS W=1u L=0.18u
.ends
X1 in out buf
.end
