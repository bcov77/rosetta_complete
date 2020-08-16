#!/usr/bin/env python


height = 20
disp_start = 10
width_p1 = 25

first_col = 12+2
top = height - 1 -1 - 4
for i in range(5):
    row_start = (top + i)*width_p1 + disp_start
    print("@buf_ram_%i = 1"%row_start)
    for j in range(8):
        print("@buf_ram_%i = @buf_big%i_%i"%(row_start + 1 + first_col + j, i, j))

print("#############")

first_col = 12+2
top = height - 1 -1 - 4 - 6
for i in range(5):
    row_start = (top + i)*width_p1 + disp_start
    print("@buf_ram_%i = 1"%row_start)
    for j in range(8):
        print("@buf_ram_%i = @buf_big%i_%i"%(row_start + 1 + first_col + j, i, j))