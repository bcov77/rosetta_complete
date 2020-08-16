#!/usr/bin/env python

height = 20
disp_start = 10
width_p1 = 25

for i in range(height-1):
    store_off = width_p1*i + disp_start
    from_off = width_p1*(i-1) + disp_start
    print("def shift1_%i():"%(i))
    print("    @buf_ram_%i = 1"%(store_off))
    for j in range(10):
        if ( i > 0 ):
            print("    @buf_ram_%i = @buf_ram_%i"%(store_off + j + 2, from_off + j + 2))
        else:
            print("    @buf_ram_%i = 'aaI'"%(store_off + j + 2))

for i in range(height-1):
    store_off = width_p1*i + disp_start
    from_off = width_p1*(i-2) + disp_start
    print("def shift2_%i():"%(i))
    print("    @buf_ram_%i = 1"%(store_off))
    for j in range(10):
        if ( i > 1 ):
            print("    @buf_ram_%i = @buf_ram_%i"%(store_off + j + 2, from_off + j + 2))
        else:
            print("    @buf_ram_%i = 'aaI'"%(store_off + j + 2))

for i in range(height-1):
    store_off = width_p1*i + disp_start
    from_off = width_p1*(i-3) + disp_start
    print("def shift3_%i():"%(i))
    print("    @buf_ram_%i = 1"%(store_off))
    for j in range(10):
        if ( i > 2 ):
            print("    @buf_ram_%i = @buf_ram_%i"%(store_off + j + 2, from_off + j + 2))
        else:
            print("    @buf_ram_%i = 'aaI'"%(store_off + j + 2))


for i in range(height-1):
    store_off = width_p1*i + disp_start
    from_off = width_p1*(i-4) + disp_start
    print("def shift4_%i():"%(i))
    print("    @buf_ram_%i = 1"%(store_off))
    for j in range(10):
        if ( i > 3 ):
            print("    @buf_ram_%i = @buf_ram_%i"%(store_off + j + 2, from_off + j + 2))
        else:
            print("    @buf_ram_%i = 'aaI'"%(store_off + j + 2))

for i in range(height-1):
    store_off = width_p1*i + disp_start
    print("def check_%i():"%(i))
    varz = []
    for j in range(10):
        varz.append("@buf_ram_%i"%(store_off + j + 2))

    print("    result = %s"%"+".join(varz))

    print("    if ( result == 180 ):")
    print("        return 1")
    print("    else:")
    print("        return 0")



print("def check_shift():")
print("    lines = 0")
for i in range(height-1-1, -1, -1):
    from_bottom = height-1-1-i
    print("    result = check_%i()"%i)
    print("    lines = lines + result")
    if ( from_bottom > 0 ):
        print("    if ( lines > 0 ):")
        print("        if ( result == 0 ):")
        print("            if ( lines == 1 ):")
        print("                shift1_%i()"%(i+1))
    if ( from_bottom > 1 ):
        print("            else:")
        print("                if ( lines == 2 ):")
        print("                    shift2_%i()"%(i+2))
    if ( from_bottom > 2 ):
        print("                else:")
        print("                    if ( lines == 3 ):")
        print("                        shift3_%i()"%(i+3))
    if ( from_bottom > 3 ):
        print("                    else:")
        print("                        if ( lines == 4 ):")
        print("                            shift4_%i()"%(i+4))

print("    if ( lines > 0 ):")
print("        if ( lines == 1 ):")
print("            shift1_0()")
print("        else:")
print("            if ( lines == 2 ):")
print("                shift2_0()")
print("                shift2_1()")
print("            else:")
print("                if ( lines == 3 ):")
print("                    shift3_0()")
print("                    shift3_1()")
print("                    shift3_2()")
print("                else:")
print("                    if ( lines == 4 ):")
print("                        shift4_0()")
print("                        shift4_1()")
print("                        shift4_2()")
print("                        shift4_3()")
print("    return lines")


