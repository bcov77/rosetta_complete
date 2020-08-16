# rosetta_complete

## Introduction

As many have probably guessed, RosettaScripts is indeed turing complete. It has probably been turing complete from very near its conception, but the addition of `StoredResidueSubsets` gave access to unlimited named variables. Combine that with the `IfMover`, the `IfThenFilter`, `ParsedProtocols`, and the `LoopOverMover` and you have control flow. Finally, the `CalculatorFilter` and `SavePoseMover` give incredible shortcuts for actually performing computations.

Printing is accomplished by mutating a pose and printing its sequence. Ironically, the `MultiplePoseMover` is probably the best for printing a pose's sequence. Key input is technically possible by loading constraint files, but an external program must generate that file on the fly.

Many of the operations performed here don't seem possible, unless you consider the idea of writing thousands of lines of xml. For instance, mathematical operations coming from the `CalculatorFilter` go through an entire array of `IfMovers` with `RangeFilters` each looking for exactly 1 int value. (It uses a binary search, so it's not <i>that</i> slow.)


This github repo contains "rosetta_complete.py" which compiles the Ros language to RosettaScripts xml. Ros is an ultra slim language that looks like python but lacks most features.

## Executing Compiled Scripts

To execute a compiled xml, the following command will work where pdb.pdb is any pdb.

```bash
rosetta_scripts -s pdb.pdb -parser:protocol compiled.xml | grep Applying
```

Often one may want to pass the output through sed to make it easier to read. The command may buffer at this point and so sed outputs often look like this: (this converts all I to " ")

```bash
stdbuf -o0 rosetta_scripts -s pdb.pdb -parser:protocol compiled.xml | stdbuf -o0 -i0 grep Applying | stdbuf -i0 -o0 sed 's/I/ /g'
```


## Example code:

`prime_numbers.ros`, `tunnel.ros`, and `tetris.ros` provide pretty good overviews of the Ros language. `tetris.ros` was the holy grail to really prove the turing completeness of the language.

Only tetris accepts key inputs. Running `tetris.ros` in one terminal and `./keyinput.py '<left><up><right><down>/'` in another will give you control. Use the arrow keys and / to control the pieces.

`tetris.xml` uses this command to run:

```bash
stdbuf -o0 rosetta_scripts -overwrite -s test.pdb -mute all -unmute protocols.rosetta_scripts.MultiplePoseMover -parser:protocol tetris.xml | stdbuf -o1880 -i0 grep --color=never Applying | stdbuf -o0 -i0 sed -e 's/I/ /g' -e 's/[VYTW]/▓/g'
```

The others work well with this command:

``` bash
stdbuf -o0 rosetta_scripts -overwrite -s test.pdb -mute all -unmute protocols.rosetta_scripts.MultiplePoseMover -parser:protocol tunnel.xml | stdbuf -o0 grep Applying | stdbuf -o0 -i0 sed -e 's/I/ /g' -e 's/W/▓/g'
```


## Ros language documentation:

### Indentation:

In Ros, all indentations (think python) must be 4 spaces.

### Numbers:

In Ros, all numbers are non-negative integers. Floating point numbers may exist briefly inside calculations, but the results are floored to an int. Overflows often clip to 0 or $MAXINT.

### Variables:

Variable work like you would expect.

```python
a = 5
b = a
```

There are many reserved variable names. In general, avoid double underscore (__), lit_*, retval, and many more.

### Chars:

All ascii chars can be accessed via `'X'` like C++. These are evaluated as integers.

All protein sequence chars may be accessed via `'aaW'`. Use these when writing to `buf[]`

### Buffers:

In Ros, there are a few buffers you can use. All but `buf[]` accept both read and writes. `buf[]` may only be written to.

`buf` -- literally a protein of size `$BUFSIZE`
`ram` -- buffer of size `$RAMSIZE`
`big0`,`big1`,`big2`,`big3`,`big4` -- The screen buffer used for the `big_*()` functions. Each `big*` is length `$BUFSIZE`
`keybuf` -- Where the `keyinput()` stores its values

Buffers are accessed like python:

```python
buf[5] = 'aaR'

ram[16] = ram[ a + b ]
```

Arbitrarily named buffers could easily be added to this project (8 lines of code). Though, the are not currently implemented.


### if:

`if` in Ros works very similarly to python except the if statement must be an expression containing: `<`, `>`, `<=`, `>=`, or `==`.

```python
if ( (x + 3) / 2 >= 7 ):
    do_something()
else:
    do_something_else()
```

`elif` is not supported. Neither is `!=`. If you need `!=`, just go straight to `else`

### Loops:

Only the `while` loop is supported and only the no-argument version is supported.

```python
while:
    do_something()
```

To break out of a loop, use `break`

```python
i = 0
while:
    if ( i == 5 ):
        break
    i = i + 1
```

`continue` is also supported.

### functions:

Functions look very much like python. But default values are not supported.

```python
def my_cool_function( arg1, arg2 ):
    return arg1 + arg2
```

All functions return exactly 1 integer value. `return` may be used anywhere inside a function. Functions without `return` return 0.

A major difference between Ros functions and python functions however, is that like C++, Ros functions can only be used once they've been declared. This means if you define `A()` then `B()`, you cannot call `B()` from `A()`. Additionally, you can't call `B()` from `B()` because `B()` isn't fully defined until after it has been parsed. So recursive functions aren't possible. There's likely no way around this limitation as it is a limitation of RosettaScripts itself.

### Expressions:

All expression in Ros are evaluated by the `CalculatorFilter`. Only these characters are allowed `*-+/()`. In order to aid parsing, every nested `( )` is evaluated separately. The effect of this is that every `( )` is effectively the python function `int( )`.

Example:

```python
a = ( 4 / 5 ) * 5

if ( a == 0 ):
    # this is what actually happens
else:
    # you would expect 4 though
```

Because the `( 4 / 5 )` is evaluated separately before the `X * 5`, `4 / 5` gets floored to `0` and the entire expression evaluates to `0`.

Boolean operations are not allowed in expressions.

Expression evaluation is really slow, avoid it where possible.


### Miscellaneous:

`pass` -- works exactly like in python (and is actually never needed in Ros)

`print()` -- prints the contents of `buf[]`

`@__script__VAR` -- Using the `@` sign, you can access the raw variable names. For the most part don't use this, but `@__script__VAR` will access "global" variables stored at `0` indent

`@buf_NAME_X` -- You can also use `@` to directly access buffers. This is much faster but requires you to know at compile time what offset you want. `buf[]` cannot be accessed this way.



### Directives:

Ros scripts may signal to the compiler certain values. Here are all options:

`$BUFSIZE` -- The size of `buf`
`$RAMSIZE` -- Length of `ram` buffer
`$MAXINT` -- The maximum integer value. Must be `2^X - 1`
`$RANDMAX` -- Max output for `rand()` function. Must be `2^X - 1`
`$WHILE_ITERS` -- The maximum number of `while` loop iterations
`$AVAIL_CHARS` -- Characters available for `big_print()`
`$CLEAR_CHAR` -- `big_print()` space char
`$PRINT_CHAR` -- `big_print()` filled char
`$BUF_CACHING` -- Either `0` or `1`. See "buf_caching" section
`$KEY_INPUT` -- Number of keys for keyinput. See "key input" section
`$KEY_INPUT_CALLS` -- Number of times `keyinput()` can be called

Storing to directives looks like this:

```
$MAXINT 1023
$AVAIL_CHARS ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789
```


### Builtins:

Ros offers many built in functions to do thing too hard to code in the actual Ros language

`big_clear()` -- clear the `big*` buffer
`big_print(char, offset)` -- write a character to the `big*` buffer at offset. Returns new offset
`big_display()` -- copy the `big*` buffer to `buf` and print each line
`rand()` -- return a random number between `0` and `$RANDMAX` inclusive
`keyinput()` --  Load keyinput data
`save("name")` -- Save `buf[]` to name `"name"`. Don't use the names `"integer"` or `"buffer"`
`load("name")` -- Load stored buf from `"name"` into `buf[]`. See buf_caching.


#### big_print():

`big_print()` offers the easiest way to actually print words and numbers from Ros.

In order to use `big_print()`, you must set `$AVAIL_CHARS` to all of the characters you plan to use. `$PRINT_CHAR` and `$CLEAR_CHAR` decide what will be used for filled and empty regions of the text.

`big_print()` is most often used like this:

```python
big_clear()
off = 10
off = big_print('H', off)
off = big_print('E', off)
off = big_print('L', off)
off = big_print('L', off)
off = big_print('O', off)
big_display()
```

See `tunnel.ros` for a way to print integers.


#### keyinput():

This is the only sad part of the Ros language because it relies on an external program. Perhaps someday someone can get Ros to actually read from stdin.

Calling `keyinput()` will cause a sequence constraint file called `keyinput.MSAcst` to be read. It is expected that `keyinput.MSAcst` refers to another file containing a PSSM constraint (here `keyinput.profile`). The value stored for Alanine is what is read. Each seqpos of the file is read into the `keybuf[]` buffer. `$NUM_KEYINPUT` determines how many keys are read.

`keyinput.py` can be used generate th `keyinput.profile`. It takes a string argument for each key you want to use. Then, each time each key is pressed, it increments the corresponding seqpos of the PSSM by 1.

Due to a hilarious twist of fate, the `ConstraintSetMover` caches each constraint it reads. This means that internally, a different `ConstraintSetMover` is used for each `keyinput()` call. `$KEY_INPUT_CALLS` specifies how many times you are allowed to call `keyinput()`


`buf_caching:`

In order to make printing faster, it's possible to cache the `buf[]` buffer such that the underlying pose does not need to be updated if the current write won't change it. This makes storing to `buf[]` slightly slower, unless your stored value is already cached in which case it is very fast.

An important caveat here is that the buffer used for caching is not directly tied to the underlying pose. Therefore, if one calls the builtin `load()`, the buffer will go stale.

If one wishes to use `load()` with `$BUF_CACHING 1`, the best option is ensure that writes to `buf[]` always go to the original buffer. (i.e. if you call `load()` on something that is out of sync with `buf[]`, be sure to `load()` the thing that's in-sync with `buf[]` before you actually store to `buf[]`)


## Actual XML implementation:

This section describes how `rosetta_complete.py` is actually able to use the RosettaScript language as an assembly language.

### Poses:

There are two poses that are used and that are created on startup by clever use of the `AddChain` mover. One is `$BUFSIZE` long and the other is `$MAXINT` long and they are both stored with `SavePoseMovers`. For 99% of execution, the `"integer"` pose is loaded. Rarely, the `"buffer"` pose is loaded when mutations need to be made or it needs to be printed.

### Variables:

All of the variables are `StoredResidueSubsets`. Specifically, they are selections of 0 or more residues starting from residue 1. These can be easily copied around with `StoreResidueSubset` and can be evaluated as filters with the `ResidueCountFilter`.

Literal values (like 4) come from a giant table of `IndexResidueSelectors` from `"lit_0"` all the way to `"lit_$MAXINT"`


### Expressions:

Expressions are first parsed into their most basic form `A*B+C`, and then converted into `CalculatorFilters`. The calculator filter is then evaluated by a huge array of `IfMovers` holding `RangeFilters` to decide what value to store to a specific result variable.

To limit the number of lines of xml, a sort of math subprocessor is used. First, all variables are stored into the math registers and another register is used to select which math expression to use. The actual math function is an `IfThenFilter` which selects from a list of calculator filters. That `IfThenFilter` is then evaluated over and over again as the `RangeFilters` try to decide what the result is.

This process uses a binary search to make it faster, but math is still really slow.


### Buffers:

Buffers are made as terribly as you're probably expecting. Every single position in the buffer is actually a `StoredResidueSubset`. Then, a binary search is used to index into a wall of `StoreResidueSubsetMovers`.

### Printing:

The actual `print()` statement is very easy, it turns out that the `MultiplePoseMover` prints the pose sequence. So one just needs to load the `"buffer"` pose, call `MultiplePoseMover`, and reload `"integer"`.

Actually mutating the `"buffer"` pose is much harder. The reason is that all of the `StoredResidueSubsets` are actually stored inside `"integer"`. So as soon as you load `"buffer"`, all of your variables disappear. It's possible to circumvent this with walls of `ParsedProtocols` though. First, a set of `$BUFSIZE` `ParsedProtocols` mark a residue on `"buffer"` with a `PDBInfoLabel`. Then, a 20-length `ParsedProtocols` wall marks the marked aa with another `PDBInfoLabel` specifying which aa to use. Finally, the `PackRotamersMover` is called with 21 task operations, 1 the prevents repacking on non-marked residues, and 20 `RestrictAbsentCanonicalAASRLT`.


### Functions:

Functions are surprisingly easy. They are simply parsed protocols which store to a specific named variable before they exit. Then, the code that called the function simply stores that variable where it needs to go. 

Function arguments are handled in the same way with the calling code storing to a few specific named variables which are then used by the function.

See the "Breaking" section for information about mid-function `return`


### If:

At the heart of `If`, is the `IfMover`. The `then` clause is one `ParsedProtocol` and the `else` clause is another. Expressions are evaluated by the `CalculatorFilter` and the result passed through different `RangeFilters` to decide on less than or greater than.

### While:

`while` loops are just `LoopOverMovers`. Each `while` loop has a variable that tells it to keep going. If something causes the loop to end, the `0` is stored to that variable and on the next iteration, the loop exists.

This is where things start to deviate from simple. First, the `LoopOverMover` isn't great at saving state. For this reason, each `LoopOverMover` starts and ends with a `SavePoseMover`. Additionally, the filter needs to be a `MoveBeforeFilter` that loads the pose because the `LoopOverMover` discards poses that fail a filter halfway through.

Leaving a loop is accomplished by "Breaking"

### Breaking:

This turned out to be the most complicated part of the whole control flow compilation. It may seem obvious what should happen when returning from an `if` statement inside a `while` loop inside a `function`, but when you consider that this is represented as 3 nested `ParsedProtocols`, actually signalling a return from the current line is tough.

From the viewpoint of control-flow compilation, `break` and `return` behave exactly the same.

The first `break` is accomplished by simply failing a filter. This causes the current `ParsedProtocol` to quit.

Subsequent `breaks` are harder. They necessitate including a filter after every single `if` and `while` call that can fail if a break was triggered inside. Additionally, the `"integer"` pose must be saved and loaded before triggering the filters because failed filters usually reset the pose (and all stored variables).


In practice, compiling a break looks like this:

1. Look back in the scope-stack for the correct structure to break (`break` breaks `while` and `return` breaks functions)

2. Identify all `while` loops along the way and set their loop variable to `0`

3. If we're returning, store the return value

4. Set all the filter variables to fail for each structure whose parent we are breaking. In the initial example, we have to tell the `if` and `while` structures to fail as soon as they return.

5. Save the current pose

6. Fail a filter

And then what happens, is that the current `ParsedProtocol` quits, the `ParsedProtocol` containing it likely quits, and the stack unrolls until we've hit the correct final level.


One more note, if a `ParsedProtocol` fails a filter, the entire mover gets flagged as a fail. If uncaught, this breaks control flow farther than one wants. The `LoopOverMover` saves the day here, because it can actually be used like a try: catch: block to wrap all parsed protcols that might fail. Simply set the iterations to 1.


### rand():

The rand function is a actually a tower of `IfMovers` that all trigger on a `FalseFilter` with `confidence="0.5"`

### keyinput():

This is the only bad part of the project because I don't know how to actually read keys from Rosetta. In principle, this is pretty simple, load a PSSM into the pose, the pose is already poly ALA, read the PSSM value for the first N residues as a score.

The hilarious part though is that since the `ConstraintSetMover` caches the value, you actually have to use a different mover for every single read.

Maybe someday someone can get rid of this dependency.




