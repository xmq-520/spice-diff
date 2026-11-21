* EXTRA x1: revision 2
V1 in 0 DC 1
R1 in n1 4.7e3
R2 n1 out 22k
C2 out 0 2p
.subckt lvl in out
R9 out 0 4k7
.ends
X1 n1 out lvl
.model NM2 N
.end
