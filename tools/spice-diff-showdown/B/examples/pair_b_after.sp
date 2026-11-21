* pair_b: revision 2 —— 一起真实改版
* 与 r1 的差别：R2 2k -> 3k；C1 删除；新增 D2 反并；model 参数 N 改
V1 in 0 DC 1
R1 in n1 1k
R2 n1 out 3k
D1 out 0 DMOD
D2 0 out DMOD
.model DMOD D(IS=1e-14 N=1.05)
.end
