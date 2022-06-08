.global __hexagon_udivsi3

.text
__hexagon_udivsi3:

{   R2 = cl0(R0)
   R3 = cl0(R1) }
{   R5:4 = combine(##0x1,#0x0)
   P0 = cmp.gtu(R1,R0) }
{   R6 = sub(R3,R2)
   R1:0 = combine(R0,R4)
   R4 = R1 ; if (P0) jumpr R31 }
{   loop0(loop_s,R6)
   R3:2 = vlslw(R5:4,R6) }
loop_s:
{   R3:2 = vlsrw(R3:2,#0x1)
   P0 = cmp.gtu(R2,R1)
   if (!P0.new) R1 = sub(R1,R2)
   if (!P0.new) R0 = add(R0,R3) }:endloop0
{   P0 = cmp.gtu(R2,R1)
   jumpr LR }
