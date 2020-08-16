#!/usr/bin/env python

import os
import sys
import re
import numpy as np

eps = 0.000001

ros_file = sys.argv[1]

with open(ros_file) as f:
    raw_ros_file = f.readlines()



directives = {
    "BUFSIZE":60,
    "MAXINT":127,
    "WHILE_ITERS":1000000,
    "RANDMAX":15,
    "AVAIL_CHARS":"ASDF",
    "RAMSIZE":20,
    "CLEAR_CHAR":'aaI',
    "PRINT_CHAR":'aaW',
    "BUF_CACHING":1,
    "NUM_KEYINPUT":0,
    "NUM_KEYINPUT_CALLS":0
}
error = False

ros = []
my_ros = []
for iline, line in enumerate(raw_ros_file):
    line = re.sub("#.*", "", line)
    if ( len(line.strip()) == 0 ):
        continue
    if ( line.startswith("$") ):
        line = line.replace("$", "")
        sp = line.split()
        value = sp[1]
        try:
            value = int(value)
        except:
            pass
        directives[sp[0]] = value
        continue
    indent = 0
    while (line.startswith("    ")):
        line = line[4:]
        indent += 1
    if ( line.startswith(" ") ):
        print("Weird indent line %i"%iline)
        error = True
        continue
    ros.append((iline+1, indent, line.strip()))

if ( error ):
    sys.exit("Inital parsing errors")

ros.append((-1, 0, "pass"))

varz = set()

buf = ""
my_ros_buf = ""

protocol = ""

protocol_stack = []

constructs = set()


def add_mover(name):
    global protocol
    protocol += '    <Add mover="%s" />\n'%name

def add_movers(names):
    global protocol
    for name in names:
        protocol += '    <Add mover="%s" />\n'%name

def add_filter(name):
    global protocol
    protocol += '    <Add filter="%s" />\n'%name

def try_new_mover(mover_type, name, skip_header=False, **kwargs):
    if ( name in constructs):
        return
    new_mover(mover_type, name, skip_header=False, **kwargs)

def new_mover(mover_type, name, skip_header=False, **kwargs):
    new_thing("MOVERS", mover_type, name, skip_header, **kwargs)

def new_filter(mover_type, name, skip_header=False, **kwargs):
    new_thing("FILTERS", mover_type, name, skip_header, **kwargs)

def new_thing(thing_type, mover_type, name, skip_header=False, **kwargs):
    global buf
    global constructs
    assert( name not in constructs )
    constructs.add(name)
    if ( not skip_header ):
        buf += "<%s>\n"%thing_type
    buf += '    <%s name="%s"'%(mover_type, name)
    for field in kwargs:
        value = kwargs[field]
        if ( value is None ):
            continue
        buf += ' %s="%s"'%(field, str(value))
    buf += " />\n"
    if ( not skip_header ):
        buf += "</%s>\n"%thing_type


# new_filter("PoseInfo", "print")
# new_mover("PoseFromSequenceMover", "create_buffer", 
#                 sequence="A"*directives['BUFSIZE'],
#                 residue_type_set="centroid")

# new_mover("PoseFromSequenceMover", "create_integer", 
#                 sequence="A"*directives['MAXINT'],
#                 residue_type_set="centroid")

def make_save_load(name):
    try_new_mover("SavePoseMover", "save_%s"%name,
                    restore_pose=0,
                    reference_name="%s"%name)

    try_new_mover("SavePoseMover", "load_%s"%name,
                    restore_pose=1,
                    reference_name="%s"%name)

translatez = {}
def translate_z(distance):
    global translatez
    if ( distance in translatez ):
        return translatez[distance]
    global buf
    global constructs
    name = "translate_z_%i"%distance
    assert( name not in constructs )
    constructs.add(name)

    buf += "<MOVERS>\n"
    buf += '    <RollMover name="%s" min_angle="0" max_angle="0" >\n'%name
    buf += '        <axis x="0" y="0" z="1" />\n'
    buf += '        <translate x="0" y="0" z="%i" /> \n'%distance
    buf += '    </RollMover>\n'
    buf += '</MOVERS>\n'

    translatez[distance] = name
    return translatez[distance]

translatey = {}
def translate_y(distance):
    global translatey
    if ( distance in translatey ):
        return translatey[distance]
    global buf
    global constructs
    name = "translate_y_%i"%distance
    assert( name not in constructs )
    constructs.add(name)

    buf += "<MOVERS>\n"
    buf += '    <RollMover name="%s" min_angle="0" max_angle="0" >\n'%name
    buf += '        <axis x="0" y="1" z="0" />\n'
    buf += '        <translate x="0" y="%i" z="0" /> \n'%distance
    buf += '    </RollMover>\n'
    buf += '</MOVERS>\n'

    translatey[distance] = name
    return translatey[distance]




saved_sizes = [0]
def fill_saved_sizes(num):
    global saved_sizes
    if ( len(saved_sizes) < num ):
        for i in range(len(saved_sizes), num):
            start_pose = saved_sizes[i-1]
            add_mover("load_s%i"%start_pose)
            add_mover(translate_z((2**(i-1))*2))
            mover_name = "add_s%i"%start_pose
            try_new_mover("AddChain", mover_name, new_chain=0, spm_reference_name="s%i"%start_pose,
                                                    scorefxn="sfxn_none", update_PDBInfo="0")
            add_mover(mover_name)
            add_mover("drop_terms")
            make_save_load("s%i"%i)
            add_mover("save_s%i"%i)
            saved_sizes.append(i)




def create_pose(size):
    rev_binary = np.array([int(x) for x in reversed(format(size, 'b'))])
    fill_saved_sizes(len(rev_binary))

    needed = np.where(rev_binary)[0]
    for i, val in enumerate(needed):
        save_name = saved_sizes[val]
        if ( i == 0 ):
            add_mover("load_s%i"%save_name)
        else:
            add_mover(translate_y(10))
            mover_name = "add_s%i"%save_name
            try_new_mover("AddChain", mover_name, new_chain=0, spm_reference_name="s%i"%save_name,
                                            scorefxn="sfxn_none", update_PDBInfo="0")
            add_mover(mover_name)
            add_mover("drop_terms")



make_save_load("integer")
make_save_load("buffer")


# add_mover("to_centroid")
add_mover("delete_all_but_1")
add_mover("polyA")
add_mover("drop_terms")
make_save_load("s0")
add_mover("save_s0")




create_pose(directives['BUFSIZE'])
add_mover("save_buffer")
create_pose(directives['MAXINT'])
add_mover("save_integer")



lit_buf = ""

literal_vars = []
lit_buf += "<RESIDUE_SELECTORS>\n"
lit_buf += '    <Not name="lit_0" selector="true" />\n'
varz.add("lit_0")
for i in range(1, directives['MAXINT']+1):
    lit_buf += '    <Index name="lit_%i" resnums="1-%i" />\n'%(i, i)
    varz.add("lit_%i"%i)
lit_buf += "</RESIDUE_SELECTORS>\n"

keyinput_buf = ""


def inteval(varname, skip_header=False):
    name = "inteval_%s"%(varname)
    if ( name in constructs ):
        return name
    new_filter("ResidueCount", name, skip_header, residue_selector=varname)
    varz.add(varname)
    return name



def make_intif(varname, size):
    global buf
    filt = inteval(varname)
    buf += "<FILTERS>\n"
    names = []
    for i in range(size):
        name = "intif__%s__%i"%(varname, i)
        new_filter("Range", name, True, 
            filter=filt,
            lower_bound=i-1, upper_bound=i+1)
        names.append(name)
    buf += "</FILTERS>\n"
    return names

intifs = []

def intif(number):
    global intifs
    if ( number >= len(intifs) ):
        var = "var_intif_%i"%number
        names = make_intif(var, directives['MAXINT'])
        intifs.append((var, names))
    return intifs[number]



def store(var_to, var_from, skip_header=False):
    name = "store__%s__%s"%(var_to, var_from)
    if ( name in constructs ):
        return name
    varz.add(var_to)
    varz.add(var_from)
    new_mover("StoreResidueSubset", name, skip_header,
                subset_name=var_to,
                residue_selector=var_from,
                overwrite=1)
    return name


def pp_start():
    global protocol
    global protocol_stack
    protocol_stack.append(protocol)
    protocol = ""

def pp_end(name, skip_header=False):
    global constructs
    global buf
    global protocol
    global protocol_stack
    assert( name not in constructs )
    constructs.add(name)
    if ( not skip_header ):
        buf += "<MOVERS>\n"

    buf += '    <ParsedProtocol name="%s" >\n'%name
    buf += protocol.replace("    ", "        ")
    buf += '    </ParsedProtocol>\n'

    if ( not skip_header ):
        buf += "</MOVERS>\n"

    protocol = protocol_stack.pop()


# store buffer backened
# store_ipos
# store_char



def make_if_mover_block(name_base, call_whos, intif_names ):
    global buf

    names = []

    buf += "<MOVERS>\n"
    for i, call_who in enumerate(call_whos):
        intif_name = intif_names[i]

        name = name_base + "__" + call_who + "__" + intif_name
        new_mover("If", name, True,
                    filter_name=intif_name,
                    true_mover_name=call_who)
        names.append(name)

    buf += "</MOVERS>\n"
    return names

ifcalls = {}

def ifcall(intif_var, intif_names, mover_base, movers):
    name = "ifcall__%s__%s"%(intif_var, mover_base)
    assert(name not in ifcalls)
    if ( name in ifcalls ):
        return ifcalls[name]

    names = make_if_mover_block(name, movers, intif_names)

    pp_start()
    add_movers(names)
    pp_end(name)

    ifcalls[name] = [name]
    return ifcalls[name]

def binary_ifcall(mover_base, movers, var=None, cache=False):
    my_movers = list(movers)


    func_name = "ifcall__binary__%s"%(mover_base)

    if ( cache ):
        if ( func_name in ifcalls ):
            return ifcalls[func_name]
    else:
        assert(func_name not in ifcalls)

    if ( var is None ):
        var = func_name + "_var"
    var_test = inteval(var)


    ifcalls[func_name] = (func_name, var)


    for i in range(100000000):
        log2 = int(round(np.log( len(my_movers) ) / np.log(2) ))
        if ( 2**log2 == len(my_movers) ):
            break
        my_movers.append("_null")

    num_movers = len(my_movers)

    range_lb_ub = []

    ranges = []
    for i in range(num_movers):
        range_lb_ub.append([i-1, i+1])


    last_level = my_movers
    ranges = range_lb_ub

    for level in range(log2-1, -1, -1):
        assert(2**(level+1) == len(last_level))

        assert(len(last_level) == len(ranges))
    
        these_names = []
        these_ranges = []
        for idx in range(2**level):
            name = "%s__%i__%i"%(func_name, level, idx)

            if ( level == 0 ):
                name = func_name

            filt1 = last_level[idx*2+0]
            filt2 = last_level[idx*2+1]
            range1 = ranges[idx*2+0]
            range2 = ranges[idx*2+1]

            new_filter("Range", name + "_range", False, 
                filter=var_test,
                lower_bound=range1[0], upper_bound=range1[1])

            new_mover("If", name, False,
                        filter_name=name + "_range",
                        true_mover_name=filt1,
                        false_mover_name=filt2)

            these_names.append(name)
            these_ranges.append([range1[0], range2[1]])
        last_level = these_names
        ranges = these_ranges

    return (func_name, var)



buf += "<RESIDUE_SELECTORS>\n"
for i in range(max(directives['BUFSIZE'], directives['NUM_KEYINPUT'])):
    buf += '    <Index name="sel_%i" resnums="%i" />\n'%(i, i+1)

buf += "</RESIDUE_SELECTORS>\n"

mark_buf_movers = []

buf += "<MOVERS>\n"
for i in range(directives['BUFSIZE']):
    name = "mark_buf_%i"%i
    pp_start()
    add_mover("save_integer")
    add_mover("load_buffer")
    new_mover("AddResidueLabel", name + "_", True,
                residue_selector="sel_%i"%i,
                label="MARK")
    add_mover(name + "_")
    add_mover("save_buffer")
    add_mover("load_integer")
    pp_end(name, True)

    mark_buf_movers.append(name)

buf += "</MOVERS>\n"


def mark_buf(var):
    mover_base = "mark_buf"
    movers = mark_buf_movers
    # intif_var, intif_names = intif(0)
    # names = ifcall(intif_var, intif_names, mover_base, movers)
    call_name, intif_var = binary_ifcall(mover_base, movers, cache=True)

    add_mover(store(intif_var, var))
    add_mover(call_name)

aa_order = "ACDEFGHIKLMNPQRSTVWY"

mark_aa_movers = []

buf += "<MOVERS>\n"
for i in range(len(aa_order)):
    aa = aa_order[i]
    name = "mark_aa_%s"%aa

    pp_start()
    add_mover("save_integer")
    add_mover("load_buffer")
    new_mover("AddResidueLabel", name + "_", True,
                label="MUT_%s"%aa,
                residue_selector="MARK")
    add_mover(name + "_")
    add_mover("save_buffer")
    add_mover("load_integer")
    pp_end(name, True)
    mark_aa_movers.append(name)
buf += "</MOVERS>\n"

remove_mark_aa_movers = []
buf += "<MOVERS>\n"
for i in range(len(aa_order)):
    aa = aa_order[i]
    name = "remove_mark_aa_%s"%aa
    new_mover("LabelPoseFromResidueSelectorMover", name, True,
                remove_property="MUT_%s"%aa,
                residue_selector="true")
    remove_mark_aa_movers.append(name)
name = "remove_mark"
new_mover("LabelPoseFromResidueSelectorMover", name, True,
            remove_property="MARK",
            residue_selector="true")
remove_mark_aa_movers.append(name)
buf += "</MOVERS>\n"

pp_start()
add_mover("save_integer")
add_mover("load_buffer")
add_movers(remove_mark_aa_movers)
add_mover("save_buffer")
add_mover("load_integer")
pp_end("remove_marks")

# new_mover("StoreResidueSubset", "_null",
#             subset_name="_null",
#             residue_selector="",
#             overwrite=1)

def set_mark_aa(var):
    mover_base = "mark_aa"
    movers = mark_aa_movers
    intif_var, intif_names = intif(0)
    names = ifcall(intif_var, intif_names, mover_base, movers)

    add_mover(store(intif_var, var))
    add_movers(names)



def fast_equal_check(var1, var2, inequal=False):
    global buf
    global constructs
    if ( inequal ):
        name = "fast_inequal__%s__%s"%(var1, var2)
    else:
        name = "fast_equal__%s__%s"%(var1, var2)
    if ( name in constructs ):
        return name

    xor = "xor__%s__%s"%(var1, var2)
    constructs.add(xor)

    buf += "<RESIDUE_SELECTORS>\n"

    buf += '    <And name="%s" >\n'%xor
    buf += '        <Or selectors="%s,%s" />\n'%(var1, var2)
    buf += '        <Not >\n'
    buf += '            <And selectors="%s,%s" />\n'%(var1, var2)
    buf += '        </Not>\n'
    buf += '    </And>\n'
    buf += "</RESIDUE_SELECTORS>\n"

    if ( inequal ):
        max_res = None
        min_res = 1
    else:
        max_res = 0
        min_res = None

    new_filter("ResidueCount", name, 
                        residue_selector=xor,
                        max_residue_count=max_res,
                        min_residue_count=min_res)
    return name


def setup_buf_caching():
    if ( not directives['BUF_CACHING'] ):
        return

    new_buffer("cache_buf", directives['BUFSIZE'])
    for i in range(directives['BUFSIZE']):
        add_mover(store("buf_cache_buf_%i"%i, "lit_21"))

    pp_start()
        
    add_mover(store(buffers["cache_buf"], "buf_var_i"))
    add_mover(store("buf_cache_buf_var", "buf_var_aa"))
    add_mover("buf_cache_buf_store")
    mark_buf("buf_var_i")
    set_mark_aa("buf_var_aa")
    add_mover("save_integer")
    add_mover("load_buffer")
    add_mover("mut_pack")
    add_mover("save_buffer")
    add_mover("load_integer")
    add_mover("remove_marks")
        
    pp_end("store_to_buf_cached")

def cache_buf(var_i, var_aa):

    add_mover(store("buf_var_i", var_i))
    add_mover(store("buf_var_aa", var_aa))

    add_mover(store(buffers["cache_buf"], "buf_var_i"))
    add_mover("buf_cache_buf_retrieve")

    inequal = fast_equal_check("buf_cache_buf_ret", "buf_var_aa", inequal=True)

    try_new_mover("If", "try_store_buf",
                filter_name=inequal,
                true_mover_name="store_to_buf_cached")

    add_mover("try_store_buf")



def store_to_buf(var_i, var_aa):
    if ( directives['BUF_CACHING'] ):
        cache_buf(var_i, var_aa)
        return

    mark_buf(var_i)
    set_mark_aa(var_aa)

    add_mover("save_integer")
    add_mover("load_buffer")
    add_mover("mut_pack")
    add_mover("save_buffer")
    add_mover("load_integer")
    add_mover("remove_marks")


pp_start()
add_mover("save_integer")
add_mover("load_buffer")
add_mover("inner_print")
add_mover("load_integer")
pp_end("print")


builtins = set()


def load_rand(functions):
    global buf
    num_rand = directives['RANDMAX'] + 1

    func_name = "__func__rand"
    ret_value = func_name + "_retvalue"

    log2 = int(round(np.log( num_rand ) / np.log(2) ))
    if ( 2**log2 != num_rand ):
        sys.exit("RANDMAX must be a power of 2 minus 1")


    buf += "<MOVERS>\n"

    stores = []
    for i in range(num_rand):
        stores.append(store(ret_value, "lit_%i"%i, True))

    last_level = stores


    for level in range(log2-1, -1, -1):
        assert(2**(level+1) == len(last_level))
    
        these_names = []
        for idx in range(2**level):
            name = "%s__%i__%i"%(func_name, level, idx)

            if ( level == 0 ):
                name = func_name

            filt1 = last_level[idx*2+0]
            filt2 = last_level[idx*2+1]

            new_mover("If", name, True,
                        filter_name="fifty_fifty",
                        true_mover_name=filt1,
                        false_mover_name=filt2)

            these_names.append(name)
        last_level = these_names


    buf += "</MOVERS>\n"

    functions["rand"] = [func_name, []]
    builtins.add(func_name)


font_data = [
0x01,0x00,0x00,0x00,0x00,0x00,
0x06,0x00,0x2C,0x12,0x12,0x24,
0x04,0x00,0x0A,0x0A,0x0A,0x0E,
0x04,0x00,0x0A,0x0A,0x04,0x04,
0x04,0x00,0x0A,0x0A,0x0E,0x0A,
0x04,0x08,0x0C,0x0E,0x0C,0x08,
0x04,0x00,0x00,0x00,0x00,0x00,
0x05,0x00,0x0E,0x1F,0x0E,0x04,
0x04,0x02,0x04,0x04,0x04,0x08,
0x04,0x00,0x0A,0x04,0x0A,0x00,
0x04,0x00,0x00,0x0E,0x0A,0x0E,
0x04,0x00,0x00,0x04,0x0E,0x04,
0x04,0x00,0x00,0x00,0x04,0x00,
0x04,0x00,0x00,0x0E,0x04,0x04,
0x04,0x07,0x02,0x01,0x06,0x00,
0x05,0x1E,0x18,0x1E,0x18,0x18,
0x04,0x06,0x04,0x04,0x0C,0x04,
0x05,0x06,0x02,0x1A,0x02,0x00,
0x04,0x0C,0x02,0x04,0x0E,0x00,
0x04,0x00,0x02,0x04,0x08,0x0E,
0x05,0x0C,0x12,0x12,0x0C,0x00,
0x05,0x16,0x18,0x10,0x10,0x00,
0x04,0x0E,0x04,0x04,0x00,0x00,
0x05,0x06,0x18,0x06,0x00,0x1E,
0x06,0x04,0x3E,0x08,0x3E,0x10,
0x05,0x18,0x06,0x18,0x00,0x1E,
0x04,0x00,0x06,0x00,0x00,0x00,
0x04,0x0E,0x08,0x0C,0x08,0x0E,
0x05,0x08,0x04,0x1E,0x04,0x08,
0x06,0x00,0x2E,0x2A,0x2A,0x2E,
0x03,0x02,0x07,0x02,0x02,0x02,
0x03,0x02,0x02,0x02,0x07,0x02,
0x01,0x00,0x00,0x00,0x00,0x00,
0x02,0x02,0x02,0x02,0x00,0x02,
0x04,0x0A,0x0A,0x0A,0x00,0x00,
0x06,0x14,0x3E,0x14,0x3E,0x14,
0x06,0x1C,0x28,0x1C,0x0A,0x3C,
0x04,0x0A,0x02,0x04,0x08,0x0A,
0x05,0x08,0x14,0x08,0x14,0x0A,
0x02,0x02,0x02,0x02,0x00,0x00,
0x03,0x02,0x04,0x04,0x04,0x02,
0x03,0x04,0x02,0x02,0x02,0x04,
0x06,0x08,0x2A,0x1C,0x2A,0x08,
0x04,0x00,0x04,0x0E,0x04,0x00,
0x03,0x00,0x00,0x02,0x02,0x04,
0x04,0x00,0x00,0x0E,0x00,0x00,
0x02,0x00,0x00,0x00,0x00,0x02,
0x04,0x02,0x02,0x04,0x08,0x08,
0x04,0x04,0x0A,0x0A,0x0A,0x04,
0x04,0x04,0x0C,0x04,0x04,0x0E,
0x04,0x0C,0x02,0x04,0x08,0x0E,
0x04,0x0C,0x02,0x04,0x02,0x0C,
0x04,0x08,0x0A,0x0E,0x02,0x02,
0x04,0x0E,0x08,0x0C,0x02,0x0C,
0x04,0x06,0x08,0x0E,0x0A,0x0E,
0x04,0x0E,0x02,0x04,0x08,0x08,
0x04,0x0E,0x0A,0x0E,0x0A,0x0E,
0x04,0x0E,0x0A,0x0E,0x02,0x0C,
0x02,0x00,0x02,0x00,0x02,0x00,
0x03,0x00,0x02,0x00,0x02,0x04,
0x04,0x02,0x04,0x08,0x04,0x02,
0x04,0x00,0x0E,0x00,0x0E,0x00,
0x04,0x08,0x04,0x02,0x04,0x08,
0x04,0x0C,0x02,0x04,0x00,0x04,
0x06,0x1C,0x02,0x1A,0x2A,0x1C,
0x04,0x04,0x0A,0x0E,0x0A,0x0A,
0x04,0x0C,0x0A,0x0C,0x0A,0x0C,
0x04,0x06,0x08,0x08,0x08,0x06,
0x04,0x0C,0x0A,0x0A,0x0A,0x0C,
0x04,0x0E,0x08,0x0C,0x08,0x0E,
0x04,0x0E,0x08,0x0C,0x08,0x08,
0x04,0x06,0x08,0x0A,0x0A,0x06,
0x04,0x0A,0x0A,0x0E,0x0A,0x0A,
0x04,0x0E,0x04,0x04,0x04,0x0E,
0x04,0x02,0x02,0x02,0x0A,0x0E,
0x04,0x0A,0x0A,0x0C,0x0A,0x0A,
0x04,0x08,0x08,0x08,0x08,0x0E,
0x04,0x0A,0x0E,0x0E,0x0A,0x0A,
0x04,0x0C,0x0A,0x0A,0x0A,0x0A,
0x04,0x0E,0x0A,0x0A,0x0A,0x0E,
0x04,0x0C,0x0A,0x0C,0x08,0x08,
0x04,0x0E,0x0A,0x0A,0x0E,0x06,
0x04,0x0C,0x0A,0x0C,0x0A,0x0A,
0x04,0x06,0x08,0x04,0x02,0x0C,
0x04,0x0E,0x04,0x04,0x04,0x04,
0x04,0x0A,0x0A,0x0A,0x0A,0x0E,
0x04,0x0A,0x0A,0x0A,0x04,0x04,
0x04,0x0A,0x0A,0x0A,0x0E,0x0A,
0x04,0x0A,0x0A,0x04,0x0A,0x0A,
0x04,0x0A,0x0A,0x04,0x04,0x04,
0x04,0x0E,0x02,0x04,0x08,0x0E,
0x04,0x04,0x0A,0x0E,0x0A,0x04,
0x04,0x08,0x08,0x04,0x02,0x02,
0x03,0x06,0x02,0x02,0x02,0x06,
0x04,0x04,0x0A,0x00,0x00,0x00,
0x04,0x00,0x00,0x00,0x00,0x0E,
0x03,0x04,0x02,0x00,0x00,0x00,
0x04,0x00,0x06,0x0A,0x0A,0x06,
0x04,0x08,0x0C,0x0A,0x0A,0x0C,
0x04,0x00,0x06,0x08,0x08,0x06,
0x04,0x02,0x06,0x0A,0x0A,0x06,
0x04,0x00,0x04,0x0A,0x0C,0x06,
0x03,0x02,0x04,0x06,0x04,0x04,
0x04,0x06,0x0A,0x06,0x02,0x0C,
0x04,0x08,0x0C,0x0A,0x0A,0x0A,
0x02,0x02,0x00,0x02,0x02,0x02,
0x04,0x02,0x00,0x02,0x0A,0x04,
0x04,0x08,0x08,0x0A,0x0C,0x0A,
0x03,0x06,0x02,0x02,0x02,0x02,
0x06,0x00,0x34,0x2A,0x2A,0x22,
0x04,0x00,0x0C,0x0A,0x0A,0x0A,
0x04,0x00,0x04,0x0A,0x0A,0x04,
0x04,0x00,0x0C,0x0A,0x0C,0x08,
0x04,0x00,0x06,0x0A,0x06,0x02,
0x04,0x00,0x0A,0x0C,0x08,0x08,
0x03,0x00,0x06,0x04,0x02,0x06,
0x03,0x04,0x06,0x04,0x04,0x02,
0x04,0x00,0x0A,0x0A,0x0A,0x0E,
0x04,0x00,0x0A,0x0A,0x04,0x04,
0x06,0x00,0x22,0x2A,0x2A,0x14,
0x04,0x00,0x0A,0x04,0x04,0x0A,
0x04,0x00,0x0A,0x0A,0x04,0x08,
0x05,0x00,0x1E,0x04,0x08,0x1E,
0x04,0x06,0x04,0x08,0x04,0x06,
0x02,0x02,0x02,0x02,0x02,0x02,
0x04,0x0C,0x04,0x02,0x04,0x0C,
0x05,0x00,0x0A,0x14,0x00,0x00,
0x04,0x0E,0x00,0x0E,0x00,0x0E,]

# def load_big_print(functions):






def load_builtins(functions):
    setup_buf_caching()

    load_rand(functions)

    load_ram()

    load_big_print(functions)

    setup_keyinput(functions)


buffers = {}

def new_buffer(name, size):
    global buffers

    var_names = []
    for i in range(size):
        var_name = "buf_%s_%i"%(name, i)
        varz.add(var_name)
        var_names.append(var_name)

    # setting values

    store_var = "buf_%s_var"%(name)
    varz.add(var_name)

    stores = []
    for var_name in var_names:
        stores.append(store(var_name, store_var))

    mover_base = "buf_%s_store"%name
    movers = stores


    # intif_var, intif_names = intif(0)
    call_name, intif_var = binary_ifcall(mover_base, movers)
    # names = ifcall(intif_var, intif_names, mover_base, movers)

    buffers[name] = intif_var

    pp_start()
    add_mover(call_name)
    pp_end(mover_base)


    # retrieving values

    ret_var = "buf_%s_ret"%name
    varz.add(var_name)

    gets = []
    for var_name in var_names:
        gets.append(store(ret_var, var_name))


    mover_base = "buf_%s_retrieve"%name
    movers = gets
    # names = ifcall(intif_var, intif_names, mover_base, movers)

    call_name, var_name = binary_ifcall(mover_base, movers, var=intif_var)

    # same intif var here so far...
    pp_start()
    add_mover(call_name)
    pp_end(mover_base)


def load_big_print(functions):
    global buf

    if ( directives['AVAIL_CHARS'] == "" ):
        return

    buf_size = directives['BUFSIZE']
    for i in range(5):
        new_buffer("big%i"%i, buf_size)

    # big_clear()
    # off = big_print(char, off)
    # big_display()

    if ( directives['CLEAR_CHAR'] in char_table):

        clear_lit = "lit_%s"%char_table[directives['CLEAR_CHAR']]

        pp_start()
        for i in range(5):
            for j in range(buf_size):
                add_mover(store("buf_big%i_%i"%(i, j), clear_lit))
        pp_end("__func__big_clear")

        builtins.add("__func__big_clear")
        functions["big_clear"] = ["__func__big_clear", []]
        add_mover(store("__func__big_clear_retvalue", "lit_0" ))


    pp_start()
    for i in range(5):

        for j in range(buf_size):
            store_to_buf("lit_%i"%j, "buf_big%i_%i"%(i, j))
        add_mover("print")

    pp_end("__func__big_display")

    builtins.add("__func__big_display")
    functions["big_display"] = ["__func__big_display", []]
    add_mover(store("__func__big_display_retvalue", "lit_0"))


    assert( directives['PRINT_CHAR'] in char_table )
    print_lit = "lit_%s"%char_table[directives['PRINT_CHAR']]


    ros_code = []

    chars_values_and_funcs = []

    for char in directives['AVAIL_CHARS']:
        char_value = ord(char)

        values = font_data[char_value * 6:(char_value+1) * 6]

        width = values[0]
        format_str = "0%ib"%width

        func = "big_print_%s"%char
        chars_values_and_funcs.append((char_value, func))

        ros_code.append((-1, 0, "def %s():"%func))

        for i, value in enumerate(values[1:]):
            binary_string = format( value, format_str)
            for j, char in enumerate(binary_string):
                if ( char == "0" ):
                    continue
                ros_code.append((-1, 1, "big%i[@__func__big_printi+%i] = %s"%(i, j, print_lit)))

        ros_code.append((-1, 1, "@__func__big_print_retvalue = @__func__big_printi+%i"%width))

    mover_base = "big_print"
    movers = []
    intif_var, intif_names = intif(0)

    sparse_intif_names = []
    for char, func in chars_values_and_funcs:
        movers.append("__func__" + func)
        sparse_intif_names.append(intif_names[char])


    buf_save = buf
    buf = ""

    names = ifcall(intif_var, sparse_intif_names, mover_base, movers)

    functions["big_print"] = ["__func__big_print", ["aa", "i"]]

    pp_start()
    add_mover(store(intif_var, "__func__big_printaa"))
    add_movers(names)
    pp_end("__func__big_print")

    builtins.add("__func__big_print")

    global my_ros_buf
    my_ros_buf += buf
    buf = buf_save


    global my_ros
    my_ros += ros_code




def load_ram():

    if ( directives['RAMSIZE'] > 0 ):
        new_buffer("ram", directives['RAMSIZE'])



def make_load_keyinput():
    global buf
    num_calls = directives['NUM_KEYINPUT_CALLS']
    assert(num_calls > 0)

    log2 = int(round(np.log( num_calls ) / np.log(2) ))
    if ( 2**log2 != num_calls ):
        sys.exit("NUM_KEYINPUT_CALLS must be a power of 2")

    num_int = directives['MAXINT'] + 1
    log2_int = int(round(np.log( num_int ) / np.log(2) ))
    if ( 2**log2_int != num_int ):
        sys.exit("MAXINT must be a power of 2 minus 1")

    int_levels = int(np.ceil(log2 / log2_int))


    int_names = []
    for i in range(int_levels):
        name = "keyinput_counter_%i"%i
        add_mover(store(name, "lit_0"))
        int_names.append(name)

    movers = []
    buf += "<MOVERS>\n"
    for i in range(num_calls):
        name = "load_keyinput_%i"%i
        new_mover("ConstraintSetMover", name, True,
                add_constraints="1",
                cst_file="keyinput.MSAcst"
                )
        movers.append(name)


    ranges = []
    for i in range(num_calls):
        these_ranges = []
        val = i
        for j in range(int_levels):
            this_val = val % num_int
            these_ranges.append((this_val-1, this_val+1))
            val //= num_int
        ranges.append(these_ranges)

    buf += "</MOVERS>\n"



    buf += "<FILTERS>\n"
    inteval_names = []
    for i in range(int_levels):
        inteval_names.append(inteval(int_names[i], True))

    func_name = "load_keyinput"

    last_level = movers
    counter = 0
    counter_steps = 0

    movers_buf = ""

    for level in range(log2-1, -1, -1):
        assert(2**(level+1) == len(last_level))

        assert(len(last_level) == len(ranges))
    
        these_names = []
        these_ranges = []
        for idx in range(2**level):
            name = "%s__%i__%i"%(func_name, level, idx)

            # if ( level == 0 ):
            #     name = func_name

            filt1 = last_level[idx*2+0]
            filt2 = last_level[idx*2+1]
            range1 = ranges[idx*2+0][counter]
            range2 = ranges[idx*2+1][counter]

            new_filter("Range", name + "_range", True, 
                filter=inteval_names[counter],
                lower_bound=range1[0], upper_bound=range1[1])

            save_buf = buf
            buf = movers_buf
            new_mover("If", name, True,
                        filter_name=name + "_range",
                        true_mover_name=filt1,
                        false_mover_name=filt2)
            movers_buf = buf
            buf = save_buf


            new_range = []
            for i in range(int_levels):
                if ( i != counter ):
                    assert(ranges[idx*2+0][i] == ranges[idx*2+1][i])
                    new_range.append(ranges[idx*2+0][i])
                else:
                    new_range.append((ranges[idx*2+0][i][0], ranges[idx*2+1][i][1]))

            these_names.append(name)
            these_ranges.append(new_range)
        last_level = these_names
        ranges = these_ranges

        counter_steps += 1
        if ( counter_steps == log2_int ):
            counter = counter + 1
            counter_steps = 0

    buf += "</FILTERS>\n"

    buf += "<MOVERS>\n"
    buf += movers_buf
    buf += "</MOVERS>\n"


    p1s = []
    for i in range(int_levels):
        pp_start()
        save_math_expr_to_var(int_names[i], [int_names[i], '+', 'lit_1'])
        name = "p1_%s"%(int_names[i])
        pp_end(name)
        p1s.append(name)


    pp_start()
    last_rollover = None
    for i in range(int_levels-1, -1, -1):

        pp_start()
        if ( not last_rollover is None ):
            check_max = fast_equal_check(int_names[i], "lit_%i"%(num_int-1))

            

            name = "if_rollover_%s"%int_names[i]
            new_mover("If", name, False,
                            filter_name=check_max,
                            true_mover_name=last_rollover)
            add_mover(name)


        if ( i > 0 ):
            add_mover(store(int_names[i-1], 'lit_0'))
        add_mover(p1s[i])

        pp_end("rollover_%s"%int_names[i])
        last_rollover = "rollover_%s"%int_names[i]


    add_mover(last_rollover)

    add_mover(last_level[0])


    pp_end("load_keyinput")



def setup_keyinput(functions):
    global buf
    global keyinput_buf
    num_keys = directives['NUM_KEYINPUT']

    if ( num_keys == 0 ):
        return

    save_buf = buf
    buf = ""

    new_buffer("keybuf", num_keys)

    inteval("keyinput_switch")


    buf += "<FILTERS>\n"
    calcs = []
    for i in range(0, num_keys):
        name = "keyinput_key_%i"%i
        new_filter("ScorePoseSegmentFromResidueSelectorFilter", name, True,
                            in_context="1",
                            residue_selector="sel_%i"%i,
                            scorefxn="sfxn_keyinput")
        calcs.append(name)


    switches = []
    for i in range(0, num_keys):
        name = "key_input_switch_%i"%i
        new_filter("Range", name, True, 
            filter="inteval_keyinput_switch",
            lower_bound=i-1, upper_bound=i+1)
        switches.append(name)

    buf += '    <IfThenFilter name="keyinput_inner" >\n'

    for i in range(0, num_keys):
        switch = switches[i]
        calc = calcs[i]

        buf += '        <IF testfilter="%s" valuefilter="%s" />\n'%(switch, calc)


    buf += '    </IfThenFilter>\n'

    buf += "</FILTERS>\n"

    keyinput_buf = buf
    buf = save_buf



    # oh dear, why oh why
    make_load_keyinput()




    add_mover(store("__func__keyinput_retvalue", "lit_0"))
    pp_start()
    add_mover("load_keyinput")
    for i in range(0, num_keys):
        add_mover(store("keyinput_switch", "lit_%i"%i))
        save_math_expr_to_var("buf_keybuf_%i"%i, ['__KEYINPUT__'])

    add_mover("clear_constraints")
    pp_end("__func__keyinput")

    builtins.add("__func__keyinput")
    functions['keyinput'] = ['__func__keyinput', []]

def render_math_stuff():
    global buf

    buf += keyinput_buf

    num_known = len(known_expressions)
    expressions = [None]*(num_known+1)
    for expr in known_expressions:
        expressions[known_expressions[expr]] = expr

    buf += "<FILTERS>\n"

    for math_var in sorted(list(math_vars)):
        inteval(math_var, True)
    inteval("math_func_switch", True)

    calcs = []
    for i in range(1, num_known+1):
        expr = expressions[i]
        name = "math_func_%i"%i

        if ( expr == "__KEYINPUT__" ):
            name = "keyinput_inner"

        else:
            expanded = " ".join(list(expr))
            expanded = expanded.replace("m", "-")
            expanded = expanded.replace("d", "/")
            expanded = expanded.replace("x", "*")
            # expanded = expanded.replace("u", "%")
            expanded = expanded.replace("p", "+")

            letters = []
            for letter in expr:
                if ( letter.upper() == letter ):
                    letters.append(letter)

            buf += '    <CalculatorFilter name="%s" equation="%s" >\n'%(name, expanded)
            for letter in letters:
                buf += '        <Var name="%s" filter="inteval_math%s" />\n'%(letter, letter)
            buf += '    </CalculatorFilter>\n'


        calcs.append(name)


    switches = []
    for i in range(1, num_known+1):
        name = "math_func_switch_%i"%i
        new_filter("Range", name, True, 
            filter="inteval_math_func_switch",
            lower_bound=i-1, upper_bound=i+1)
        switches.append(name)

    buf += '    <IfThenFilter name="math_inner" >\n'

    for i in range(1, num_known+1):
        switch = switches[i-1]
        calc = calcs[i-1]

        buf += '        <IF testfilter="%s" valuefilter="%s" />\n'%(switch, calc)


    buf += '    </IfThenFilter>\n'


    range_lb_ub = []

    ranges = []
    for i in range(directives['MAXINT']+1):
        range_lb_ub.append([i-eps, i+1])

        # name = "math_range_%i"%i
        # new_filter("Range", name, True, 
        #     filter="math_inner",
        #     lower_bound=i-eps, upper_bound=i+1)
        # ranges.append(name)

    buf += "</FILTERS>\n"

    range_lb_ub[0][0] = -1000000
    range_lb_ub[-1][1] = 10000000



    buf += "<MOVERS>\n"
    stores = []
    for i in range(directives['MAXINT']+1):
        name = "math_store_%i"%i
        new_mover("StoreResidueSubset", name, True,
                    subset_name="math_result",
                    residue_selector="lit_%i"%i,
                    overwrite=1)
        stores.append(name)

    buf += "</MOVERS>\n"


    num_int = directives['MAXINT'] + 1
    log2 = int(round(np.log( num_int ) / np.log(2) ))
    if ( 2**log2 != num_int ):
        sys.exit("MAXINT must be a power of 2 minus 1")

    func_name = "math_func"

    last_level = stores
    ranges = range_lb_ub

    for level in range(log2-1, -1, -1):
        assert(2**(level+1) == len(last_level))

        assert(len(last_level) == len(ranges))
    
        these_names = []
        these_ranges = []
        for idx in range(2**level):
            name = "%s__%i__%i"%(func_name, level, idx)

            if ( level == 0 ):
                name = func_name

            filt1 = last_level[idx*2+0]
            filt2 = last_level[idx*2+1]
            range1 = ranges[idx*2+0]
            range2 = ranges[idx*2+1]

            new_filter("Range", name + "_range", False, 
                filter="math_inner",
                lower_bound=range1[0], upper_bound=range1[1])

            new_mover("If", name, False,
                        filter_name=name + "_range",
                        true_mover_name=filt1,
                        false_mover_name=filt2)

            these_names.append(name)
            these_ranges.append([range1[0], range2[1]])
        last_level = these_names
        ranges = these_ranges




    # pp_start()
    # for i in range(directives['MAXINT']+1):
    #     name = "math_result_%i"%i
    #     new_mover("If", name, True,
    #                 filter_name=ranges[i],
    #                 true_mover_name=stores[i])
    #     add_mover(name)
    # pp_end("math_func", False)




    return


#  lhs ? rhs
# rhs - lhs
equal_low_high = {
    "==": (-eps, +eps),
    "<=": (-eps, directives['MAXINT']*100),
    "<": (0, directives['MAXINT']*100),
    ">": (-directives['MAXINT']*100, 0),
    ">=": (-directives['MAXINT']*100, eps)
}


used_equalities = {}

def render_equality_stuff():
    global buf
    inteval("equal_lhs")
    inteval("equal_rhs")
    inteval("equal_func_switch")

    num_known = len(used_equalities)
    expressions = [None]*(num_known+1)
    for expr in used_equalities:
        expressions[used_equalities[expr]] = expr

    buf += "<FILTERS>\n"
    buf += '    <CalculatorFilter name="equal_inner" equation="rhs - lhs" >\n'
    buf += '        <Var name="rhs" filter="inteval_equal_rhs" />\n'
    buf += '        <Var name="lhs" filter="inteval_equal_lhs" />\n'
    buf += '    </CalculatorFilter>\n'

    calcs = []
    for i in range(1, num_known+1):
        expr = expressions[i]
        name = "equal_expr_%i"%i

        low, high = equal_low_high[expr]

        buf += '    <Range name="%s_" filter="equal_inner" lower_bound="%s" upper_bound="%s" />\n'%(
                            name, str(low), str(high))

        # stupid range doesn't have report_sm implemented
        buf += '    <CompoundStatement name="%s" >\n'%name
        buf += '        <AND filter_name="%s_"/>\n'%name
        buf += '    </CompoundStatement>\n'


        calcs.append(name)


    switches = []
    for i in range(1, num_known+1):
        name = "equal_func_switch_%i"%i
        new_filter("Range", name, True, 
            filter="inteval_equal_func_switch",
            lower_bound=i-1, upper_bound=i+1)
        switches.append(name)

    buf += '    <IfThenFilter name="equal_filter" threshold="0.5" lower_threshold="true" >\n'

    for i in range(1, num_known+1):
        switch = switches[i-1]
        calc = calcs[i-1]

        buf += '        <IF testfilter="%s" valuefilter="%s" />\n'%(switch, calc)

    buf += '    </IfThenFilter>\n'


    buf += "</FILTERS>\n"


def perform_equality(var1, var2, equality, name, then_func, else_func):
    global buf
    add_mover(store("equal_lhs", var1))
    add_mover(store("equal_rhs", var2))

    assert(equality in equal_low_high)

    if ( not equality in used_equalities ):
        used_equalities[equality] = len(used_equalities)+1

    equal_func = used_equalities[equality]

    add_mover(store( "equal_func_switch", "lit_%i"%equal_func))

    fbreak = get_fbreak_name(name)
    add_mover(store( fbreak, "lit_0" ) )
    new_filter("ResidueCount", "test_" + fbreak, 
                        residue_selector=fbreak,
                        max_residue_count=0)

    save_buf = buf
    buf = ""
    new_mover("If", name,
                filter_name="equal_filter",
                true_mover_name=then_func,
                false_mover_name=else_func)

    new_mover("LoopOver", "catch_outer_" + name,
                                  mover_name=name,
                                  filter_name="true_filter",
                                  iterations=1
                                  )
    if_buf = buf
    buf = save_buf
    add_mover("catch_outer_" + name)

    return if_buf


def prepare_while_loop(new_func_name):
    global buf

    loop_name = new_func_name + "__loop"
    var_name = new_func_name + "__var"
    test_var_name = "test_%s"%(var_name)

    new_filter("ResidueCount", "inner_" + test_var_name, 
                        residue_selector=var_name,
                        max_residue_count=0)

    new_filter("MoveBeforeFilter", test_var_name,
                        mover="load_integer",
                        filter="inner_" + test_var_name)

    add_mover(store(var_name, "lit_1"))

    fbreak = get_fbreak_name(new_func_name)
    add_mover(store( fbreak, "lit_0" ) )
    new_filter("ResidueCount", "test_" + fbreak, 
                        residue_selector=fbreak,
                        max_residue_count=0)


    add_mover("save_integer")

    save_buf = buf
    buf = ""


    new_mover("LoopOver", "catch_" + new_func_name,
                                  mover_name=new_func_name,
                                  filter_name="true_filter",
                                  iterations=1
                                  )

    new_mover("LoopOver", loop_name,
                                  mover_name="catch_" + new_func_name,
                                  filter_name=test_var_name,
                                  iterations=directives['WHILE_ITERS'],
                                  drift=1,
                                  )
    while_buf = buf
    buf = save_buf

    add_mover(loop_name)

    return while_buf



letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

known_expressions = {}
math_vars = set()

def save_math_expr_to_var(var_name, tokens):

    expr = ""
    letter_no = 0
    for itok, token in enumerate(tokens):
        if ( token == "__KEYINPUT__" ):
            expr = "__KEYINPUT__"
            assert(len(tokens) == 1)
            continue
        if ( token == "-" ):
            expr += "m"
            continue
        if ( token == "/" ):
            expr += "d"
            continue
        if ( token == "*"):
            expr += "x"
            continue
        # if ( token == "%" ):
        #     expr += "u"
        #     continue
        if ( token == "+" ):
            expr += "p"
            continue
        letter = letters[letter_no]
        letter_no += 1
        name = "math%s"%letter
        add_mover(store( name, token))
        math_vars.add(name)
        expr += letter
        
    if ( not expr in known_expressions ):
        known_expressions[expr] = len(known_expressions)+1

    math_func = known_expressions[expr]

    add_mover(store( "math_func_switch", "lit_%i"%math_func))

    add_mover("math_func")

    add_mover(store( var_name, "math_result"))






char_table = {}

for i, aa in enumerate(aa_order):
    char_table['aa%s'%aa] = str(i)

for i in range(128):
    char_table[chr(i)] = str(i)

def char_lookup(match):
    match = match.group(0)
    if (match[1:-1] not in char_table):
        sys.exit("Unknown char %s"%match)
    return char_table[match[1:-1]]

def replace_chars(line):
    return re.sub(r"'[^']+'", char_lookup, line)

def replace_lits(line):
    return re.sub(r"\b([0-9]+)\b", r"lit_\1", line)

math_chars = "*/+-,"

token_chars = "*/+-[](),"

def tokenize(expression):
    tokens = []
    cur_tok = ""
    for i, char in enumerate(expression):
        if ( char == " " ):
            if ( cur_tok != "" ):
                tokens.append(cur_tok)
                cur_tok = ""
            continue
        if ( char in token_chars ):
            if ( cur_tok != "" ):
                tokens.append(cur_tok)
                cur_tok = ""
            tokens.append(char)
            continue
        cur_tok += char
    if ( cur_tok != "" ):
        tokens.append(cur_tok)
    return tokens



def find_scopes(tokens):
    scopes = []
    scope_stack = []
    last_was_math_char = True
    for i, token in enumerate(tokens):
        math_char = False
        if ( token in math_chars ):
            math_char = True
        if ( token == "(" ):
            if ( last_was_math_char ):
                scope_stack.append(["(", len(scope_stack), i, None])
            else:
                scope_stack.append(["f#%s"%tokens[i-1], len(scope_stack), i-1, None])
            math_char = True
        if ( token == "[" ):
            assert( not last_was_math_char )
            scope_stack.append(["[%s"%tokens[i-1], len(scope_stack), i-1, None])
            math_char = True

        if ( token == ")" ):
            if ( scope_stack[-1][0] == "(" ):
                scope_stack[-1][3] = i
                scopes.append(scope_stack.pop())
            elif (scope_stack[-1][0].startswith("f#") ):
                scope_stack[-1][3] = i 
                scopes.append(scope_stack.pop())
            else:
                sys.exit("Unmatched (")

        if ( token == "]" ):
            if ( scope_stack[-1][0].startswith("[") ):
                scope_stack[-1][3] = i
                scopes.append(scope_stack.pop())
            else:
                sys.exit("Unmatched [")


        last_was_math_char = math_char

    # if ( first_pass ):
    #     scopes = scope_args(tokens, scopes)

    return scopes


def replace_scope(scope_type, tokens, new_number, new_context, functions):
    var_name = new_context + "__tmp%i"%new_number

    if ( scope_type.startswith("[") ):

        assert(len(tokens) == 4)
        var = tokens[2]
        the_buffer = tokens[0]
        assert(the_buffer in buffers)
        add_mover(store(buffers[the_buffer], var))
        add_mover("buf_%s_retrieve"%the_buffer)
        add_mover(store(var_name, "buf_%s_ret"%the_buffer))

        return var_name

    if ( scope_type == "(" ):
        math_expr = tokens[1:-1]
        if ( len(math_expr) == 0 ):
            return None
        if ( len(math_expr) == 1 ):
            return math_expr[0]

        save_math_expr_to_var(var_name, math_expr)

        return var_name

    if ( scope_type.startswith("f#") ):
        real_func_name = scope_type[2:]
        func_name = real_func_name.replace("__func__", "")
        retval = real_func_name + "_retvalue"

        my_params = parse_func_params(tokens[2:-1])

        args = functions[func_name][1]
        if ( len(args) != len(my_params)):
            sys.exit("Wrong number of args to func %s"%func_name)

        for arg, param in zip(args, my_params):
            real_arg = real_func_name + arg
            add_mover(store(real_arg, param))

        if ( real_func_name in builtins ):
            add_mover(real_func_name)
        else:
            add_mover("catch_outer_" + real_func_name)
            add_mover("load_integer")

        add_mover(store(var_name, retval))
        return var_name

def translate_tokens(tokens, my_locals, functions):
    new_tokens = []
    for token in tokens:
        if (len(token) == 1 and token in token_chars):
            new_tokens.append(token)
            continue
        if ( token.startswith("@") ):
            new_tokens.append(token[1:])
            continue
        if ( token.startswith("lit_") ):
            new_tokens.append(token)
            continue
        if ( token in my_locals ):
            new_tokens.append(my_locals[token])
            continue
        if ( token in functions ):
            new_tokens.append(functions[token][0])
            continue
        if ( token in buffers):
            new_tokens.append(token)
            continue
        sys.exit("Unknown variable %s"%token)
    return new_tokens

# things inside brackets and inside function args don't get scoped properly
def add_parenthesis(expression):
    expression = expression.replace("(", "((").replace(")", "))")
    expression = expression.replace(",", "),(")
    expression = expression.replace("[", "[(").replace("]", ")]")
    return "(" + expression + ")"


def handle_expression(expression, number, context, my_locals, functions):
    expression = add_parenthesis(expression)
    tokens = tokenize(expression)

    tokens = translate_tokens(tokens, my_locals, functions)

    return handle_expression_tokens(tokens, number, context, functions)

def handle_expression_tokens(tokens, number, context, functions):

    new_number = 0
    while len(tokens) > 1:
        # print(tokens)

        scopes = find_scopes(tokens)
        # print(scopes)

        next_scope = sorted(scopes, key=lambda x: x[1])[-1]
        
        new_context = context + "__%i"%number

        scope_type, depth, start, end = next_scope

        new_token = replace_scope(scope_type, tokens[start:end+1],
                                        new_number, new_context, functions)
        if ( new_token is None ):
            tokens = tokens[:start] + tokens[end+1:]
        else:
            tokens = tokens[:start] + [new_token] + tokens[end+1:]


        # tokens[start:end+1] = handle_expression_tokens(tokens, new_number, new_context)

        new_number += 1
    
        
    assert(tokens[0] in varz)
    return tokens[0]

def parse_func_params(innards):
    params = []
    for i, tok in enumerate(innards):
        if ( i % 2 == 1 ):
            assert(tok == ",")
            continue
        params.append(tok)
    return params

def parse_function_line(line):
    tokens = tokenize(line)
    assert(tokens[0] == "def")
    assert(tokens[2] == "(" )
    assert(tokens[-1] == ":")
    assert(tokens[-2] == ")")

    func_name = tokens[1]
    innards = tokens[3:-2]

    params = parse_func_params(innards)


    return func_name, params

def parse_if_line(line):

    tokens = tokenize(line)

    assert(tokens[0] == "if")
    assert(tokens[-1] == ":")

    if ( tokens[1] == "(" ):
        assert(tokens[-2] == ")")
        innards = tokens[2:-2]
    else:
        innards = tokens[1:-1]

    the_oper = None
    for i, expr in enumerate(equal_low_high):
        if ( expr in innards ):
            j = innards.index(expr)
            the_oper = expr
            lhs = " ".join(innards[:j])
            rhs = " ".join(innards[j+1:])

    if ( the_oper is None ):
        sys.exit("No recognized operators in if")

    return lhs, rhs, the_oper

def make_empty_else(new_func_name_if):
    new_func_name_else = new_func_name_if[:-len("__if")] + "__else"
    pp_start()
    add_mover("save_integer")
    pp_end(new_func_name_else)
    return new_func_name_else


def get_fbreak_name(elem_context):
    assert(not elem_context.startswith("__func__"))
    func_name = elem_context
    if ( elem_context.endswith("__if") ):
        func_name = elem_context[:-len("__if")]
    if ( elem_context.endswith("__else") ):
        func_name = elem_context[:-len("__else")]
    return func_name + "__fbreak"

def handle_elem_finish(final_elem_context):
    fbreak = get_fbreak_name(final_elem_context)

    add_mover("load_integer")
    add_filter("test_" + fbreak)


def control_break(nest, current_elem_context, break_type):
    all_elem_contexts = [current_elem_context]
    for nest_item in reversed(nest):
        all_elem_contexts.append(nest_item[1])

    return_satisfied = break_type != "return"
    breaks = []
    for elem_context in all_elem_contexts:
        is_if = elem_context.startswith("__iffunc")
        is_while = elem_context.startswith("__while")
        is_func = elem_context.startswith("__func__")

        if ( break_type == "return" ):
            breaks.append(elem_context)
            if ( is_func ):
                return_satisfied = True
                break
        else:
            if ( is_func ):
                sys.exit("Can't %s from a function!"%(break_type))
            breaks.append(elem_context)
            if ( is_while ):
                break
    if ( not return_satisfied ):
        sys.exit("Return outside of a function!")

    for elem_context in breaks[:-1]:
        if ( elem_context.startswith("__while") ):
            add_mover(store(elem_context + "__var", "lit_0"))
        fbreak = get_fbreak_name(elem_context)
        add_mover(store(fbreak, "lit_1"))

    final_break = breaks[-1]
    if ( final_break.startswith("__while") ):
        add_mover(store(final_break + "__var", "lit_0"))

    add_mover("save_integer")
    add_filter("false_filter")



    # is_lame = True
    # for char in special_chars:
    #     if ( char in )
    # return rhs



# def get_context(nest):
#     return "script"

# ros parsing

functions = {}
if_buf_on_else = {}
while_buf_on_while = {}

load_builtins(functions)


my_ros.append((-1, 0, "ENDOFMYROS"))
ros = my_ros + ros


my_locals = {}


nest = []
while_stack = []

context = "__script__"
elem_context = context
context_elems = 0


for iline, indent, line in ros:

    try:
        # context = get_context(nest)

        final_elem_context = None
        while ( indent != len(nest) ):

            # if without else, we need to make the else
            if ( not final_elem_context is None and final_elem_context.endswith("__if") ):
                extra_buf = if_buf_on_else[ make_empty_else(final_elem_context) ]
                buf += extra_buf

            if ( not final_elem_context is None and (final_elem_context.endswith("__if")
                                              or final_elem_context.endswith("__else")
                                              or final_elem_context.startswith("__while") ) ):
                handle_elem_finish(final_elem_context)


            if ( indent > len(nest) ):
                sys.exit("Unexpected indent line %i"%iline)

            if ( elem_context.startswith("__func__") ):
                func_name = context.replace("__func__", "")
                if ( not functions[func_name][2] ):
                    add_mover(store(context + "_retvalue", "lit_0"))
                add_mover("save_integer")

            # while handles drift itself
            if ( elem_context.startswith("__while") ):
                add_mover("save_integer")

            if ( elem_context.startswith("__if") ):
                add_mover("save_integer")

            if ( elem_context.startswith("__else") ):
                add_mover("save_integer")


            final_elem_context = elem_context

            pp_end(elem_context)

            if ( elem_context.endswith("__else" ) ):
                buf += if_buf_on_else[ elem_context ]

            if ( elem_context.startswith("__while") ):
                buf += while_buf_on_while[ elem_context ]
                while_stack.pop()

            if ( elem_context.startswith("__func__") ):
                new_mover("LoopOver", "catch_outer_" + elem_context,
                                  mover_name=elem_context,
                                  filter_name="true_filter",
                                  iterations=1
                                  )

            context, elem_context, maybe_my_locals, maybe_context_elems = nest.pop()
            if ( not maybe_my_locals is None):
                my_locals = maybe_my_locals
            if ( not maybe_context_elems is None):
                context_elems = maybe_context_elems

        line = replace_chars(line)
        line = replace_lits(line)
        # print(line)

        # else must be the first keyword after the unindenting otherwise we miss
        #   the empty else
        if ( line == "else:" ):
            if ( not final_elem_context.endswith("__if") ):
                sys.exit("Else without if")

            new_func_name_else = final_elem_context[:-len("__if")] + "__else"

            nest.append((context, elem_context, None, None ) )

            pp_start()
            elem_context = new_func_name_else
            continue
        else:
            # if without else, we need to make the else
            if ( not final_elem_context is None and final_elem_context.endswith("__if") ):
                extra_buf = if_buf_on_else[ make_empty_else(final_elem_context) ]
                buf += extra_buf

        if ( not final_elem_context is None and (final_elem_context.endswith("__if")
                                              or final_elem_context.endswith("__else")
                                              or final_elem_context.startswith("__while") ) ):
            handle_elem_finish(final_elem_context)


        protocol += "# %i "%iline + line.replace("<", "lt").replace(">", "gt") + "\n"

        if ( line == "ENDOFMYROS" ):
            buf += my_ros_buf
            continue

        if ( line == "pass" ):
            continue

        match = re.match(r'save\( *"([A-Z0-9a-z_]+)" *\)', line )
        if ( not match is None ):
            name = match.group(1)
            make_save_load(name)
            add_mover("save_integer")
            add_mover("load_buffer")
            add_mover("save_%s"%name)
            add_mover("load_integer")
            continue

        match = re.match(r'load\( *"([A-Z0-9a-z_]+)" *\)', line )
        if ( not match is None ):
            name = match.group(1)
            make_save_load(name)
            add_mover("save_integer")
            add_mover("load_%s"%name)
            add_mover("save_buffer")
            add_mover("load_integer")
            continue

        if ( line == "print()" ):
            add_mover("print")
            continue

        if ( line == "continue" ):
            control_break(nest, elem_context, "continue")
            continue

        if ( line == "break" ):
            control_break(nest, elem_context, "break")
            continue


        if ( line.startswith("def ") ):
            assert(line.endswith(":"))
            assert(context == "__script__")
            func_name, args = parse_function_line(line)
            new_func_name = "__func__" + func_name
            # [2] == return was called
            functions[func_name] = [new_func_name, args, False]

            nest.append( (context, elem_context, my_locals, context_elems) )

            my_locals = {}
            for arg in args:
                my_locals[arg] = new_func_name + arg
                varz.add(my_locals[arg])

            pp_start()
            context = new_func_name
            elem_context = new_func_name
            context_elems = 0

            continue

        if ( line.startswith("if " )):
            assert(line.endswith(":"))

            new_func_name = "__iffunc%i__%s"%(context_elems, context)
            new_func_name_if = new_func_name + "__if"
            new_func_name_else = new_func_name + "__else"


            context_elems += 1

            lhs, rhs, oper = parse_if_line(line)
            lh_var = handle_expression(lhs, 0, context, my_locals, functions)
            rh_var = handle_expression(rhs, 1, context, my_locals, functions)


            if_buf = perform_equality(lh_var, rh_var, oper, new_func_name, 
                                    new_func_name_if, new_func_name_else)
            if_buf_on_else[new_func_name_else] = if_buf

            nest.append((context, elem_context, None, None ) )

            pp_start()
            elem_context = new_func_name_if
            # context remains unchanged
            continue

        if ( line == "while:" ):

            new_func_name = "__whilefunc%i__%s"%(context_elems, context)

            context_elems += 1

            while_buf = prepare_while_loop(new_func_name)
            while_buf_on_while[new_func_name] = while_buf

            nest.append((context, elem_context, None, None))
            while_stack.append(new_func_name)
            pp_start()
            elem_context = new_func_name
            # context remains unchanged

            # we save and load the pose to ensure it drifts
            add_mover("load_integer")
            continue


        if ( ":" in line ):
            sys.exit("Can't have : in line")

        # todo handle return inside while loops
        return_control_break = False
        if ( line.startswith("return ") or line == "return" ):
            assert(context.startswith("__func__"))
            if ( line == "return" ):
                line = "return lit_0"
            line = line.replace("return", "_retvalue =")
            # only mark true if we are on the final indent of the function
            if ( elem_context.startswith("__func__") ):
                functions[context.replace("__func__", "")][2] = True
            else:
                return_control_break = True

        if ( "=" not in line ):
            my_locals["_noret"] = context +  "_noret"
            line = "_noret =" + line

        if ( "=" in line ):

            sp = [x.strip() for x in line.split("=")]
            assert(len(sp ) == 2)

            lhs, rhs = sp

            rhs_var = handle_expression(rhs, 0, context, my_locals, functions)

            # test for buffer storage
            match = re.match(r"^([A-Za-z0-9]+)\[(.*)\]$", lhs)
            if ( not match is None ):

                the_buffer = match.group(1)
                expr = match.group(2)

                lhs_var = handle_expression(expr, 1, context, my_locals, functions)

                if ( the_buffer == "buf" ):
                    store_to_buf(lhs_var, rhs_var)
                else:
                    assert(the_buffer in buffers)

                    add_mover(store(buffers[the_buffer] , lhs_var))
                    add_mover(store("buf_%s_var"%the_buffer , rhs_var))
                    add_mover("buf_%s_store"%the_buffer)

                continue

            # normal assignment operator
            assert(len(lhs.split()) == 1)

            assert(not lhs.startswith("lit_"))
            if ( lhs.startswith("@")):
                add_mover(store(lhs[1:], rhs_var))
            else:
                my_locals[lhs] = context + lhs

                add_mover(store(my_locals[lhs], rhs_var))


        if ( return_control_break ):
            control_break(nest, elem_context, "return")



    except SystemExit as e:
        print(e)
        sys.exit("Error on line %i"%iline)

if ( len(nest) != 0 ):
    print(nest)
    assert(False)



# add_mover("print")





























varz_text = "#varz \n"
varz_text += "<RESIDUE_SELECTORS>\n"
for var in varz:
    if (var.startswith("lit_") ):
        continue
    varz_text += '    <StoredResidueSubset name="%s" subset_name="%s" />\n'%(var, var)

varz_text += "</RESIDUE_SELECTORS>\n"



with open("rosetta_complete_backend.xml") as f:
    backend = f.read().replace("</ROSETTASCRIPTS>", "")


new_name = ros_file.replace(".ros", "") + ".xml"

with open(new_name, "w") as f:
    f.write(backend)

    f.write(varz_text)
    f.write(lit_buf)

    main_buf = buf
    buf = ""
    
    render_math_stuff()
    render_equality_stuff()

    f.write(buf)
    f.write(main_buf)

    f.write("<PROTOCOLS>\n")
    f.write(protocol)
    f.write("</PROTOCOLS>\n")

    f.write('<OUTPUT scorefxn="sfxn_none" />\n')
    f.write("</ROSETTASCRIPTS>\n")













print("Successfuly compiled %s"%ros_file)







