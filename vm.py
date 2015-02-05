#!/usr/bin/python3
from sys import argv
from collections import namedtuple, defaultdict
from re import compile
from ntpath import basename
from pprint import pprint

# Buffers
content = []
tok_buffer = []
tok_defs = [stat_tokens]
context = [statement]

# Token definitions 
stat_tokens = [
    ['EQUALS'      , '=='              ],
    ['GREATERTHEN' , '>='              ],
    ['AND'         , '&&'              ],
    ['OR'          , '\\|\\|'          ],
    ['ASSIGN'      , '='               ],
    ['GREATER'     , '>'               ],
    ['SUM'         , '\\+'             ],
    ['MUL'         , '\\*'             ],
    ['SUB'         , '-'               ],
    ['SQR'         , '\\^'             ], #TODO Not implemented in parser
    ['CONCAT'      , '\\$'             ],

    ['QUOTE'       , "'"               ],
    ['DQUOTE'      , '"'               ],

    ['IF'          , '(\\?|if|IF)'     ], # If statement
    ['ELSE'        , '(else|ELSE|\\:)' ], # Else for if
    ['DEF'         , '(def|DEF)'       ], # Define function
    ['PRINT'       , '(print|PRINT)'   ], # Print result of next stat
    ['ILN'         , 'ILN'             ], # Return line from input
    ['INPUT'       , '(input|INPUT)'   ], # Assign input to variable
    ['RETURN'      , '(ret|RET)'       ], # Return result of block
    ['WHILE'       , '(while|WHILE)'   ], # While cycle
    ['NOT'         , '(not|NOT|\\!)'   ], # Negation
    ['LOAD'        , '(load|LOAD)'     ], # Load file
    ['CODE'        , '(code|CODE)'     ], # Return statement without eval
    ['EXEC'        , '(exec|EXEC)'     ], # Execute code in variable
    ['LBRAC'       , '\\('             ],
    ['RBRAC'       , '\\)'             ],

    ['IGNORE'      , '#\\{[^\\}]*\\}'  ], # Multiline comment

    ['IGNORE'      , '(#[^\n]*\n)'     ], # Single line comment

    ['IGNORE'      , ' +'              ],

    ['NUMBER'      , '(0|[1-9][0-9]*)' ],
    ['TERM'        , '[a-zA-Z0-9_\\\\]+'],
]

stat_tokens = [[name, compile(pattern)] for name, pattern in stat_tokens]

def statement(name, match):
    """ Clasic statement, probably in infix """
    print(name, match)
    if name == 'DQUOTE':
        tok_buffer.append(name)
        tok_defs.append(ustr_tokens)
        context.append(ustring)
    elif name == 'TERM':
        tok_buffer.append(name)
        tok_defs.append(term_tokens)
        context.append(term)
        parse_line(match.group(0))
    elif name == 'QUOTE':
        tok_buffer.append(name)
        tok_defs.append(str_tokens)
        context.append(string)
    elif name == 'NUMBER': tok_buffer.extend([name, match.group(0)])
    elif name != 'IGNORE': tok_buffer.append(name)


def indent():
    
    match = indent.pattern.match(content[-1])
    act_indent = int(len(match.group(0))/4)

    while act_indent > indent.size:
        indent.size += 1
        tok_buffer.append('START_BLOCK')

    while act_indent < indent.size:
        indent.size -= 1
        tok_buffer.append('END_BLOCK')
    
    content[-1] = content[-1][len(match.group(0)):]

indent.pattern = compile('( {4})*')
indent.size = 0

# Parsing string statement

str_tokens = [
    ['TEXT', "[^'\\\\]+"],
    ['ESCAPE', "\\\\(.)"],
    ['QUOTE', "'"]
]

str_tokens = [[name, compile(pattern)] for name, pattern in str_tokens]

def string(name, match):
    if name == 'TEXT':
        tok_buffer.extend([name, match.group(0)])
    elif name == 'ESCAPE':
        tok_buffer.extend([name, match.group(1)])
    elif name == 'QUOTE':
        tok_defs.pop(-1)
        context.pop(-1)

# Unescaped string parsing

ustr_tokens = [
    ['TEXT', '[^"\\\\$]+'],
    ['ESCAPE', "\\\\(.)"],
    ['STAT', "\\$([^ \n]+)"],
    ['DQUOTE', '"']
]

ustr_tokens = [[name, compile(pattern)] for name, pattern in ustr_tokens]

def ustring(name, match):
    if name == 'TEXT':
        tok_buffer.extend([name, match.group(0)])
    elif name == 'ESCAPE':
        tok_buffer.extend([name, match.group(1)])
    elif name == 'DQUOTE':
        tok_defs.pop(-1)
        context.pop(-1)
    elif name == 'STAT':
        tok_buffer.append(name)
        tok_defs.append(stat_tokens)
        context.append(statement)
        parse_line(match.group(1))

# Parsing term

term_tokens = [
    ['DS', '/'],
    ['NAME', '[a-zA-Z][a-zA-Z0-9_]*'],
]

term_tokens = [[name, compile(pattern)] for name, pattern in term_tokens]

def term(name, match):
    """ We are in the term """
    tok_buffer.append(name)
    if name == 'NAME':
        tok_buffer.append(match.group(0))

def parse_line(line):
    content.append(line)

    matched = True

    if context[-1] == statement: indent()

    while len(content[-1]) > 0 and matched:

        matched = False

        for name, pattern in tok_defs[-1]:
            match = pattern.match(content[-1])
            if match:
                context[-1](name, match)
                content[-1] = content[-1][len(match.group(0)):]
                matched = True
                break

