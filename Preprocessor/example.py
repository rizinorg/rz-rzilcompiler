#!/usr/bin/env python3

from encodings import utf_8
import pprint
import re

# General approach:
#
# Search for all syntax and behavior pairs.
# Remove leading whitespace.
# Remove a single space leading and/or trailing every character.
# Use two matching groups and the whitespace inbetween them to infer a block being syntax or behavior from the second one being empty or not.


# Open file. And read into memory.
with open(
    "../ressources/Hexagon/Hexagon-manuals-80-n2040-45-b-v67-AND-80-n2040-44-b-v66-hvx.txt",
    encoding="utf_8",
) as g:
    testpages = g.read()
g.close()

# 0 "Syntax +Behavior\n(.+?)(?=Class|80-N)"gms
# 1  Syntax +Behavior\n matches the starting line for instruction pairs
# 2  (.+?) is grouping the actual instructions inbetween syntax behavior pairs
# 3  (?=Class|80-N) is a positive lookahead for either the Class description or a new page.
# 2(?=3) results in matching every character between a newline after Behavior and before either Class or 80-N.
# All in all one can find all Syntax-Behavior groups in the manual with this regex.
sb_groups = re.compile(r"Syntax +Behavior\n(.+?)(?=Class|80-N)", flags=re.S | re.M)

# 0 "^([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+) *([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+)?"gm
# 1  ^([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+) captures every character at the start of a line in group 1
# 2   * matches any potential whitespace between both groups
# 3  ([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+)? captures a potential second group but is omitted if there no spaces after the first group.
# 1-3 together lets us find each syntax behavior pair in two capturing groups. If there is only on group found it has to be a behavior
# group otherwise first is syntax and second is behavior.
sb_pairs = re.compile(
    r"^([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+) *([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+)?",
    flags=re.M,
)

# Returns an iterator for each syntax behavior block.
sb = sb_groups.finditer(testpages)

for match in sb:
    # Strips all the leading whitespace at the start of each line aswell as a single space leading and/or trailing from a single character from the content of the syntax behavior groups.
    cleaned_groups = re.sub(r"^\s+", "", match.group(1), flags=re.M)
    cleaned_groups = re.sub(r" ?([^ ]) ?", r"\1", cleaned_groups)
    # There is a special case in which a single space divides a syntax and behavior group so we need to add that back. The only occurence we've found so far was infront of a for.
    cleaned_groups = re.sub(r"for", " for", cleaned_groups)
    Syntax = ""
    Behavior = ""
    sb_dict = dict()
    consecutive = False
    b_check = False
    # We split each syntax behavior block into two matching groups and use some nested logic to add them to a dictonary.
    for index, item in enumerate(sb_pairs.findall(cleaned_groups)):
        # There are two blocks since the second matching groups is not empty.
        if item[1]:
            # TODO work out the kinks of syntax behavior blocks that grow in parallel
            if "if" in item[0]:
                print("This is suspicious.")
            # We can add our instruction pair to the dictonairy and start a new one if we know that we either visited a double block or a single behavior block beforehand.
            if consecutive or b_check:
                sb_dict[Syntax] = Behavior
                Syntax = item[0]
                Behavior = item[1]
                b_check = False
                consecutive = True
            #
            else:
                Syntax += item[0]
                Behavior += item[1]
                consecutive = True
                b_check = True
        # Only one matching group has content so it has to be a behavior entry.
        else:
            Behavior += " " + item[0]
            consecutive = False
            b_check = True

    # We need to add the last pair manually as we finished the for loop.
    sb_dict[Syntax] = Behavior
    pprint.pprint(sb_dict)


# Now replace `[!], [.new]` constructs and build multiple instances of this single syntax.
# After all syntax <> behavior pairs were parsed. Match each syntax to its instruction.
# Count how many syntax could not be matched to an instruction. Or if there were duplicats. Stuff like this.
# Investigate the cases when no instruction could be matched to the syntax. What happend here? Error in parser? Instruction simply doesn't exists?

# CASES TO BE AWARE OF
#
# Multiple lines of syntax
#
# Syntax                                Behavior
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
#
# Syntax                                Behavior
#
# if ([!]Pv)                            if ([!]Pv[0]) {
# vmem(Rx++#s3):nt=Os8.new                   EA=Rx;
#                                            *(EA&~(ALIGNMENT-1)) = OsN.new;
#                                            Rx=Rx+#s*VBYTES;
#                                       } else {
#                                            NOP;
#                                       }
#
# `if` is in the syntax, but the syntax is only one line. Though the behavior consists of multiple lines:
#
# Syntax                                Behavior
#
# if ([!]Pv) vmem(Rt+#s4)=Os8.new       if ([!]Pv[0]) {
#                                            EA=Rt+#s*VBYTES;
#                                            *(EA&~(ALIGNMENT-1)) = OsN.new;
#                                       } else {
#                                            NOP;
#                                       }
#
# Multiple lines of syntax but each of which is a single instructuction.
#
# Syntax                                     Behavior
#
# Cd=Rs                                      Cd=Rs;            --------> First instruction
# Cdd=Rss                                    Cdd=Rss;          --------> Second instruction
# Rd=Cs                                      Rd=Cs;            --------> Etc.
# Rdd=Css                                    Rdd=Css;
#
# Syntax and instruction are only seperated by a _single_ space
#
# Syntax                                     Behavior
#
# Vd.ub=vasr(Vu.uh,Vv.uh,Rt)[:rnd]:sat for (i = 0; i < VELEM(16); i++) {     -------------> Single space before `for` seperates syntax and behavior
#                                                 shamt = Rt & 0x7;
#                                                 Vd.uh[i].b[0]=usat8(Vv.uh[i] +
#                                            (1<<(shamt-1)) >> shamt);
#                                                 Vd.uh[i].b[1]=usat8(Vu.uh[i] +
#                                            (1<<(shamt-1)) >> shamt) ;
#                                            }
