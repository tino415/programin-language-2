# programing-language-2

## Implemented controll structures

### Conditions

Condition is like python withou :, als there is alias of if to ? and of else to :

**if** #Condition
    # Code
**else**
    # Code

If returns result of statement behind or else statement, so something like this is posible

    res = if a > b:
        a = a - b
        ret a
    else
        a = b - a
        ret b

Also if has alias ? and else :, and if you write statement inline with if and else, return value is returned directli, so you dont need to use return keyword

    res = ? a > b a - b : b - a

### While

In this language there is implemented classic while statement

    while #Condition
        #Code to do

Or

    while #Condition #Code to do

Example:

    while true print 'Hello world'

## Global and local variables

Variables are divided into local and global,

To define gloval variable you have to assign value to it like:

    \a = 3

Now you can acces this variable from other files like

    file_where_defined\a

## Functions

To define function there is keyword **def**

**def** funcName param1 param2
    \# Content of the functions

There is one namespace for the functions, so functions defined inside functions are accessible from every where

## Other keywords

**code** Passes statement behind unevaluated, (you can assign block of code to variable or pass to function)

**exec** To execute code in variable

**ret** Return value of the block

**print** Print result of next statement

**not** or **!** Negate result of next statement

**load** load external file

**ILN** Return one line from input

## Input line (ILN)

Return one line from input, enables interesting construction like

    print ? (var = ILN) == 3 'You writed 3' : 'You dont wirted 3'

This construction assigns one line from input to var, compare it to 3 and printed message acording to it

