#!/usr/bin/env python
import sys,tty,termios
import os

letters = sys.argv[1]

letters = letters.replace("<left>", "D").replace("<up>", "A").replace("<down>", "B").replace("<right>", "C")

counts = [0]*len(letters)

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

buf = []
while True:
    key = getch()
    buf.append(key)
    if ( buf[0] == '\x1b' ):
        if (len(buf) != 3 ):
            continue
        key = buf[-1]
        buf = [key]
        

    if ( buf[0]  == "X" ):
        break

    key = buf.pop()
    if ( key in letters ):
        idx = letters.index(key)
        counts[idx] += 1

    print(counts)

    with open("tmp", "w") as f:
        f.write("aa A C D E F G H I K L M N P Q R S T V W Y\n")
        for count in counts:
            f.write("A %i"%count + " 0"*19 + "\n")
    os.rename("tmp", "keyinput.profile")




