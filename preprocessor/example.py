#!/usr/bin/env python3

from encodings import utf_8
from operator import le
import re


# "(Syntax +Behavior)[\n ]+(([rR][a-zA-Z=(,#0-9);<>]+)[\n ]+([rR][a-zA-Z=(,#0-9) <>;]+)[\n ]+)+"gms
# /(Syntax +Behavior)[\n ]+(([rR][a-zA-Z=(,#0-9);<>]+)[\n ]+([rR][a-zA-Z=(,#0-9) <>;]+)[\n ]+)+/gms
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
with open("testpages.txt", encoding='utf_8') as g:
    testpages = g.read()

is_bhv = False               # Flag: In syntax/behavior section.
pos_mult_line_stx = False    # Flag: Marks if the syntax in the current line could continue in the next line.
sb_pairs = []                # List of syntax <> behavior pairs. A pair is of the type dictonary.
stx_line = 0                 # Syntax can span over multiple lines. Here we count those lines.

pattern = re.compile(r"Syntax +Behavior\n(.+?)(?=Class|80-N)",flags=re.S | re.M)
# 0 "Syntax +Behavior\n(.+?)(?=Class|80-N)"gms
# 1  Syntax +Behavior\n matches the starting line for instruction pairs
# 2  (.+?) is grouping the actual instructions inbetween syntax behavior pairs
# 3  (?=Class|80-N) is a positive lookahead for either the Class description or a new page.
# 2(?=3) results in matching every character between a newline after Behavior and before either Class or 80-N.
# All in all one can find all Syntax-Behavior groups in the manual with this regex.

groups = re.compile(r"^([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+) *([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+)?", flags= re.M)
# 0 "^([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+) *([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+)?"gm
# 1  ^([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+) captures every character at the start of a line in group 1
# 2   * matches any potential whitespace between both groups
# 3  ([\w\d,;:+?\-%&$~[\]\}{.(#!)<>=]+)? captures a potential second group but is omitted if there no spaces after the first group.
# 1-3 together lets us find each syntax behavior pair in two capturing groups. If there is only on group found it has to be a behavior 
# group otherwise first is syntax and second is behavior.


iter = pattern.finditer(testpages)

for match in iter:
    str = re.sub(r"^\s+", "", match.group(1), flags = re.M) # strips all the leading whitespace from each line
    str = re.sub(r" ?([^ ]) ?", r'\1', str)                 # replaces a single space leading and/or trailing a character with just the character
    str = re.sub(r"for"," for",str)                         # there has to be a more clever way of doing this but that space is missing from a 
                                                            # syntax behavior block and makes certian for loops unseperable
    content = groups.findall(str)
    print(0)
    Syntax = ""
    Behavior = ""
    lexikon = dict()
    consecutive = False
    bcheck = False
    for index, item in enumerate(content):
        if item[1]: # Es gibt zwei Matches und wir haben jeweils einen Eintrag für Syntax mit item[0] und Behavior mit item[1]. 
            if "{" in item[1] and "if" in item[0] and consecutive:    # Es könnte potentiell eine Ausnahme geben und die Syntax auch eine in der nächsten Zeile ein weiteres Token dazubekommen.
                print("This is very sus.")
            # Hier müssen wir überprüfen ob zwei doppelt gefüllte Zeilen aufeinander folgen. Denn dann haben wir ein neues Paar aus Syntax/Behavior.
            if consecutive or bcheck:
                print("We are consecutive, Sir!")
                lexikon[Syntax] = Behavior
                Syntax = item[0]
                Behavior = item[1]
                bcheck = False
            else:
                Syntax += item[0]
                Behavior += item[1]
                print("Hmm fresh meat.")
                consecutive = True
        else:   # Es gibt nur einen Match und wir haben nur einen Eintrag für Behavior mit item[1].
            Behavior += " "+item[0]
            consecutive = False
            bcheck = True        
            
            
    print(lexikon)

# Falls eine neue Zeile nur ein Element hat, muss sie dem Behavior der vorherigen Zeile hinzugefügt werden.
# Falls man nach dem Hinzufügen zu Behavior wieder zwei Elemente vorfindet, gilt es ein neues Paar zu bauen. 
g.close()

# for l in f:
    # Entering the Syntax/Behavior section in the manual.
#    if re.find('^\s+Syntax\s+Behavior', l):
#        in_bhv = True
#        stx_line +=
    # Leaving the syntax/behavior section in the manual.
#    if re.find('^\s+Class:'):
#        in_bhv = False

    # NO need to process lines which have no usefull information for us.
#    if not in_bhv:
#        continue

    # Behavior only line. If the syntax is in the same line it wouldn't have that many leading spaces.
#    if re.find('^\s{,32}', l):    
        # -> strip spaces
        # -> add behavior line to the current syntax/behavior pair
#        pass
#    else:
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
