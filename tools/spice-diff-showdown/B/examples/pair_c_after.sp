* pair_c: 与 before 只差 buf 里的 R1 阻值
V1 in 0 DC 1
.subckt buf in out
R1 out 0 2k
M1 out in 0 0 NMOS W=1u L=0.18u
.ends
X1 in out buf
.end
