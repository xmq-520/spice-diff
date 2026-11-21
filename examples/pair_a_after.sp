* pair_a: revision 1 重排后 —— 与 before 结构完全等价
* 行序打乱、refdes 对调、内部节点改名 n1->n9、数值换写法 1k->1000 / 1MEG->1e6 / 2K->2000
* 参数次序对调；端口声明次序不变
.param SUPPLY=1.8

.subckt buf in out
R3 out 0 1e6
M1 out in 0 0 nmos L=0.18U w=2U
.ends

C1 n9 0 10p
R2 n9 out 2000
R1 in n9 1000
V1 in 0 dc 1
.end
