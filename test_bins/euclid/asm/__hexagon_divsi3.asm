
.global __hexagon_divsi3

.text
__hexagon_divsi3:
{   R1 = abs(R0)
   R2 = abs(R1) }
{   P0 = cmp.gt(R0,##-0x1)
   P1 = cmp.gt(R1,##-0x1) }
{   R3 = cl0(R1)
   R4 = cl0(R2)
   R5 = sub(R1,R2)
   P2 = cmp.gtu(R2,R1) }
{   P1 = xor(P0,P1)
   R0 = ##0x0
   P0 = cmp.gtu(R2,R5) }
{   if (P2) jumpr:nt LR }
{   R0 = mux(P1,##-0x1,#0x1)
   R4 = sub(R4,R3) }
{ R3 = ##0x1 ; if (P0) jumpr R31 }
{   loop0(l_start,R4)
   R3:2 = vlslw(R3:2,R4)
   R0 = ##0x0 }
l_start:
{   R3:2 = vlsrw(R3:2,#0x1)
   P0 = cmp.gtu(R2,R1)
   if (!P0.new) R1 = sub(R1,R2)
   if (!P0.new) R0 = add(R0,R3) }:endloop0
{   P0 = cmp.gtu(R2,R1)
   if (!P1) jumpr:nt LR
   if (!P0.new) R0 = add(R0,R3) }
{   R0 = sub(##0x0,R0)
   jumpr LR }

