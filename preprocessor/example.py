#!/usr/bin/env python3

import re


# "(Syntax +Behavior)[\n ]+(([rR][a-zA-Z=(,#0-9);<>]+)[\n ]+([rR][a-zA-Z=(,#0-9) <>;]+)[\n ]+)+"gms

#
# CASES TO BE AWARE OF
#

# Multiple lines of syntax

# Syntax                                     Behavior
#
# p[01]=cmp.eq(Rs,#-1); if              P[01]=(Rs==-1) ? 0xff : 0x00 if
# ([!]p[01].new) jump:<hint>            ([!]P[01].new[0]) {
# #r9:2                                     apply_extension(#r);
#                                           #r=#r & ~PCALIGN_MASK;
#                                           PC=PC+#r;
#                                       }
# p[01]=cmp.eq(Rs,#U5); if              P[01]=(Rs==#U) ? 0xff : 0x00 if
# ([!]p[01].new) jump:<hint>            ([!]P[01].new[0]) {
# #r9:2                                     apply_extension(#r);
#                                           #r=#r & ~PCALIGN_MASK;
#                                           PC=PC+#r;
#                                       }

# Multiple lines of syntax but each of which is a single instructuction.

# Syntax                                     Behavior
#
# Cd=Rs                                      Cd=Rs;            --------> First instruction
# Cdd=Rss                                    Cdd=Rss;          --------> Second instruction
# Rd=Cs                                      Rd=Cs;            --------> Etc.
# Rdd=Css                                    Rdd=Css;

# Syntax and instruction are only seperated by a _single_ space

# Syntax                                     Behavior
#
# Vd.ub=vasr(Vu.uh,Vv.uh,Rt)[:rnd]:sat for (i = 0; i < VELEM(16); i++) {     -------------> Single space before `for` seperates syntax and behavior
#                                                 shamt = Rt & 0x7;
#                                                 Vd.uh[i].b[0]=usat8(Vv.uh[i] +
#                                            (1<<(shamt-1)) >> shamt);
#                                                 Vd.uh[i].b[1]=usat8(Vu.uh[i] +
#                                            (1<<(shamt-1)) >> shamt) ;
#                                            }
# 


# Open file. And read into memory.
with open("../manual.txt") as g:
    f = g.readlines()

is_bhv = False               # Flag: In syntax/behavior section.
pos_mult_line_stx = False    # Flag: Marks if the syntax in the current line could continue in the next line.
sb_pairs = []                # List of syntax <> behavior pairs. A pair is of the type dictonary.
stx_line = 0                 # Syntax can span over multiple lines. Here we count those lines.

for l in f:
    # Entering the Syntax/Behavior section in the manual.
    if re.find('^\s+Syntax\s+Behavior', l):
        in_bhv = True
        stx_line +=
    # Leaving the syntax/behavior section in the manual.
    if re.find('^\s+Class:'):
        in_bhv = False

    # NO need to process lines which have no usefull information for us.
    if not in_bhv:
        continue

    # Behavior only line. If the syntax is in the same line it wouldn't have that many leading spaces.
    if re.find('^\s{,32}', l):    
        # -> strip spaces
        # -> add behavior line to the current syntax/behavior pair
        pass
    else:
        # This line contains syntax. Either it belongs to the previous lines syntax
        # OR we have a new syntax.
        # TODO ---> How to know which one is the case?
        # Maybe an `if` in the syntax indicates that the syntax in the next line belongs to the previous?
        # Because the behavior is much longer for `if` containing syntaxes and spans over multiple lines as well?

        # Example:
        # if ([!]Pv)                            if ([!]Pv[0]) {
        # vmem(Rx++#s3):nt=Os8.new                   EA=Rx;
        #                                            *(EA&~(ALIGNMENT-1)) = OsN.new;
        #                                            Rx=Rx+#s*VBYTES;
        #                                       } else {
        #                                            NOP;
        #                                       }
        #
        
        # Another example. `if` in the syntax, but the syntax is only one line. Though the behavior consists of multiple lines:

        # if ([!]Pv) vmem(Rt+#s4)=Os8.new       if ([!]Pv[0]) {
        #                                            EA=Rt+#s*VBYTES;
        #                                            *(EA&~(ALIGNMENT-1)) = OsN.new;
        #                                       } else {
        #                                            NOP;
        #                                       }
        #  

        # How to split the line into syntax and behavior:
        # The syntax seems to have no spaces in it, besides one exception!
        # The exceptions are `if statements`:
        #       ` if (..) <blabla>`.
        # 
        # Therefore we remove the spaces before/after the brackets and the `if`.
        # Now the syntax has no spaces in it what so ever.
        # The spaces after the syntax string always mark the start of the behavior.

        # At this space the syntax and behavior can be splitted.
        # 
        # -> Strip spaces at beginning and end of line.
        # -> Remove the space after the `if` and its brackets (in behavior and syntax alike. Use re.sub()).
        # -> Split syntax and behavior along the spaces which seperates them.
        # -> Set the flag if a the syntax could continue in the next line.
        # -> Append syntax to previous syntax if it belongs to it
        # -> Append behavior.
        # -> Fail if no behavior could be found.
        # -> Catch any other fails.

# Now replace `[!], [.new]` constructs and build multiple instances of this single syntax.

# After all syntax <> behavior pairs were parsed. Match each syntax to its instruction.
# Count how many syntax could not be matched to an instruction. Or if there were duplicats. Stuff like this.
# Investigate the cases when no instruction could be matched to the syntax. What happend here? Error in parser? Instruction simply doesn't exists?
