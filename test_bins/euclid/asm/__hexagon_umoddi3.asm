
.global __hexagon_umoddi3
.text

{   R6 = cl0(R1:0)
   R7 = cl0(R3:2)
   R5:4 = combine(R3,R2)
   R3:2 = combine(R1,R0) }
{   R10 = sub(R7,R6)
   R1:0 = combine(##0x0,#0x0) }
{  R15:14 = combine(##0x0,#0x1) }
{   R13:12 = lsl(R5:4,R10)
   R15:14 = lsl(R15:14,R10)
   R11 = add(R10,##0x1) }
{   loop0(0xa4f4,R11)
   P0 = cmp.gtu(R5:4,R3:2) }
{   if (P0) jump:nt loc.hexagon_umoddi3_return }
{   P0 = cmp.gtu(R13:12,R3:2) }
{   R7:6 = sub(R3:2,R13:12)
   R9:8 = add(R1:0,R15:14) }
{   R1:0 = vmux(P0,R1:0,R9:8)
   R3:2 = vmux(P0,R3:2,R7:6) }
{   R15:14 = lsr(R15:14,#0x1)
   R13:12 = lsr(R13:12,#0x1) }:endloop0
loc.hexagon_umoddi3_return:
{   R1:0 = combine(R3,R2)
   jumpr LR }

