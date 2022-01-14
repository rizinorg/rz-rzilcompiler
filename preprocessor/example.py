#!/usr/bin/env python3

import re


# "(Syntax +Behavior)[\n ]+(([rR][a-zA-Z=(,#0-9);<>]+)[\n ]+([rR][a-zA-Z=(,#0-9) <>;]+)[\n ]+)+"gms

#
# CASES TO BE AWARE OF
#

# Multiple lines of syntax

#                   p[01]=cmp.eq(Rs,#-1); if              P[01]=(Rs==-1) ? 0xff : 0x00 if
#                   ([!]p[01].new) jump:<hint>            ([!]P[01].new[0]) {
#                   #r9:2                                     apply_extension(#r);
#                                                             #r=#r & ~PCALIGN_MASK;
#                                                             PC=PC+#r;
#                                                         }
#                   p[01]=cmp.eq(Rs,#U5); if              P[01]=(Rs==#U) ? 0xff : 0x00 if
#                   ([!]p[01].new) jump:<hint>            ([!]P[01].new[0]) {
#                   #r9:2                                     apply_extension(#r);
#                                                             #r=#r & ~PCALIGN_MASK;
#                                                             PC=PC+#r;
#                                                         }

# Multiple lines of syntax but each of which is a single instructuction.

#                   Cd=Rs                                      Cd=Rs;
#                   Cdd=Rss                                    Cdd=Rss;
#                   Rd=Cs                                      Rd=Cs;
#                   Rdd=Css                                    Rdd=Css;


is_bhv = False # In syntax/behavior section
sb_pairs = []  # List of syntax <> behavior pairs.
stx_line = 0   # Syntax can span over multiple lines. Here we count those lines.

with open("../manual.txt") as f:
    for l in f.readlines():
        if re.find('^\s+Syntax\s+Behavior', l):
            in_bhv = True
            stx_line +=
        if re.find('^\s+Class:'):
            in_bhv = False
   
        if not in_bhv:
            continue

        if re.find('^\s{,32}', l):
            
            # Behavior only line. If the syntax is in the same line it wouldn't have that many leading spaces.
            # -> strip spaces
            # -> add behavior line to the current syntax
            pass
        else:
            stx_line += 1 # The syntax spans over mutliple lines. OR we have a new syntax.

            #TODO ---> How to find this out?
            # Maybe an `if` in the syntax indicates that the syntax in the next line belongs to the preivous?
            # Because the behavior is much longer for `if` containing syntax and spans over multiple lines as well?

            # How to split the line into syntax and behavior:
            # The syntax seems to have no spaces in it.
            # One exception is ` if (..) <blabla>`. Therefore we remove the spaces before/after the brackets and the `if` preemptively.
            # After the syntax is always a space which seperates it from the behavior.
            # At this space the syntax and behavior can be splitted.
            # 
            # -> Remove the space after the `if` and its brackets (in behavior and syntax alike. Use re.sub()).
            # -> Split syntax and behavior along the space which seperates them.
            # -> Append syntax to previous syntax if it belongs to it
            # -> Append behavior.
            # -> Fail if no behavior could be found.
            # -> Catch any other fails.
            
            # If new syntax block.
            sb_pairs.append({'syntax': extracted_syntax, 'behavior': extracted_behavior})

    # After all syntax <> behavior pairs were parsed. Match each syntax to its instruction.
    # If non instruction could be found -> raise exception -> investigate.
