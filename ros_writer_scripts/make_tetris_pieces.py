#!/usr/bin/env python

import numpy as np

pieces_text = """
0000
1111

0010
0010
0010
0010

0000
0000
1111

0100
0100
0100
0100

110
011

001
011
010

110
011

010
110
100

011
110

010
011
001

011
110

100
110
010

11
11

11
11

11
11

11
11

001
111

010
010
011

000
111
100

110
010
010

111
001

010
010
110

100
111

011
010
010

000
111
010

010
110
010

010
111

010
011
010


"""



pieces = []
cur_piece = []
for line in pieces_text.split("\n"):
    line = line.strip()
    if (len(line) == 0):
        if ( len(cur_piece) > 0 ):
            pieces.append(np.array(cur_piece))
            cur_piece = []
        continue
    a = np.zeros((len(line)), np.bool)
    for i, letter in enumerate(line):
        if ( letter == "1" ):
            a[i] = True
    cur_piece.append(a)


#x=14
#y=0 is the pieces initial position
for ipiece, piece in enumerate(pieces):
    bump_start = ipiece <= 3

    positions = np.array(list(np.where(piece))).T
    if ( bump_start ):
        positions[:,0] -= 1


    if ( piece.shape[1] >= 2 ):
        positions[:,1] -= 1

    positions[:,1] -= 10


    print("def write_shape_%i(x, y, val):"%(ipiece))
    for y in np.unique(positions[:,0]):
        print("    ram[(y+%i)*@__script__width_p1+@__script__disp_start] = 1"%(y))
    for pos in positions:
        print("    ram[(y+%i)*@__script__width_p1+x+%i+@__script__disp_start] = val"%(pos[0],pos[1]))

    print("def check_shape_%i(x, y):"%(ipiece))
    print("    to_ret = 'aaI'")
    for pos in positions:
        print("    off = (y+%i)*@__script__width_p1+x+%i+@__script__disp_start"%(pos[0],pos[1]))
        print("    val = ram[off]")
        print("    if ( val == 'aaI' ):")
        print("        pass")
        print("    else:")
        print("        if ( val == 'aaV'):" )
        print("            return 'aaV'")
        print("        if ( val == 'aaY'):" )
        print("            return 'aaY'")
        print("        if ( val == 'aaW'):" )
        print("            to_ret = 'aaW'")
    print("    return to_ret")


#24 shapes

print("def write_shape(x, y, val, ishape):")
print("    if ( ishape >= 24 ):")
for i in range(24, 28):
    print("        if ( ishape == %i ):"%i)
    print("            return write_shape_%i(x, y, val)"%i)
print("    if ( ishape < 12 ):")
print("        if ( ishape < 6 ):")
print("            if ( ishape < 3 ):")
for i in range(0, 3):
    print("                if ( ishape == %i ):"%i)
    print("                    return write_shape_%i(x, y, val)"%i)
print("            else:")
for i in range(3, 6):
    print("                if ( ishape == %i ):"%i)
    print("                    return write_shape_%i(x, y, val)"%i)
print("        else:")
print("            if ( ishape < 9 ):")
for i in range(6, 9):
    print("                if ( ishape == %i ):"%i)
    print("                    return write_shape_%i(x, y, val)"%i)
print("            else:")
for i in range(9, 12):
    print("                if ( ishape == %i ):"%i)
    print("                    return write_shape_%i(x, y, val)"%i)
print("    else:")
print("        if ( ishape < 18 ):")
print("            if ( ishape < 15 ):")
for i in range(12, 15):
    print("                if ( ishape == %i ):"%i)
    print("                    return write_shape_%i(x, y, val)"%i)
print("            else:")
for i in range(15, 18):
    print("                if ( ishape == %i ):"%i)
    print("                    return write_shape_%i(x, y, val)"%i)
print("        else:")
print("            if ( ishape < 21 ):")
for i in range(18, 21):
    print("                if ( ishape == %i ):"%i)
    print("                    return write_shape_%i(x, y, val)"%i)
print("            else:")
for i in range(21, 24):
    print("                if ( ishape == %i ):"%i)
    print("                    return write_shape_%i(x, y, val)"%i)


print("def check_shape(x, y, ishape):")
print("    if ( ishape >= 24 ):")
for i in range(24, 28):
    print("        if ( ishape == %i ):"%i)
    print("            return check_shape_%i(x, y)"%i)
print("    if ( ishape < 12 ):")
print("        if ( ishape < 6 ):")
print("            if ( ishape < 3 ):")
for i in range(0, 3):
    print("                if ( ishape == %i ):"%i)
    print("                    return check_shape_%i(x, y)"%i)
print("            else:")
for i in range(3, 6):
    print("                if ( ishape == %i ):"%i)
    print("                    return check_shape_%i(x, y)"%i)
print("        else:")
print("            if ( ishape < 9 ):")
for i in range(6, 9):
    print("                if ( ishape == %i ):"%i)
    print("                    return check_shape_%i(x, y)"%i)
print("            else:")
for i in range(9, 12):
    print("                if ( ishape == %i ):"%i)
    print("                    return check_shape_%i(x, y)"%i)
print("    else:")
print("        if ( ishape < 18 ):")
print("            if ( ishape < 15 ):")
for i in range(12, 15):
    print("                if ( ishape == %i ):"%i)
    print("                    return check_shape_%i(x, y)"%i)
print("            else:")
for i in range(15, 18):
    print("                if ( ishape == %i ):"%i)
    print("                    return check_shape_%i(x, y)"%i)
print("        else:")
print("            if ( ishape < 21 ):")
for i in range(18, 21):
    print("                if ( ishape == %i ):"%i)
    print("                    return check_shape_%i(x, y)"%i)
print("            else:")
for i in range(21, 24):
    print("                if ( ishape == %i ):"%i)
    print("                    return check_shape_%i(x, y)"%i)







