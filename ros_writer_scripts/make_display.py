#!/usr/bin/env python

import os
import sys

width = int(sys.argv[1])
height = int(sys.argv[2])
spare = int(sys.argv[3])





print("def display():")
print('    save("buf_save")')

for i in range(height):
    ram_start = spare + i * (width + 1)
    print("    if ( @buf_ram_%i == 1 ):"%ram_start )
    print("        @buf_ram_%i = 0 "%ram_start)
    print('        load("buf_save")')
    for j in (range(width)):
        print("        buf[%i] = @buf_ram_%i"%(j, ram_start + j + 1))
    print('        save("display_%i")'%i)
    print('        save("buf_save")')

for i in range(height):
    print('    load("display_%i")'%(i))
    print('    print()')

print('    load("buf_save")')
