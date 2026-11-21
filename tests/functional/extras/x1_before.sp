* EXTRA x1: revision 1
V1 in 0 DC 1
R1 in n1 4k7
R2 n1 out 10k
.subckt lvl in out
R9 out 0 5k
.ends
X1 n1 out lvl
.model NM2 N
.end
