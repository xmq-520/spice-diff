* pair_a: revision 1 — 原始写法
* 纯重排/重命名/换数值写法的对照组，期望零差异
V1 in 0 DC 1
R1 in n1 1k
R2 n1 out 2K
C1 n1 0 10p
.subckt buf in out
M1 out in 0 0 NMOS W=2u L=0.18u
R3 out 0 1MEG
.ends
.param supply=1.8
.end
