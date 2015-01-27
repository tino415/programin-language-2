#!/usr/bin/python3
from sys import argv
from collections import namedtuple, defaultdict
from re import compile
from ntpath import basename

"""
As simple as possible complete programming language interpreter, all calls are 
done in infix and contain no complex constructs,
    
    ./main.py file_path
"""

path = argv[1]
functions = {}
globvars = {}

def lexical_analisys(content):
    """ Transform stream of chars into tokens recursively """

    class Token:
        """ Class representing one token """
        def __init__(self, name, pattern, value = None):
            self.name = name
            self.pattern = compile(pattern)
            self.value = value
        def match(self, content): return self.pattern.match(content)
    
    def tokenize(token_defs, content):
        matched = True
        while len(content) > 0 and matched:
            matched = False
            for token in token_defs:
                match = token.match(content)
                if match:
                    if token.name != 'IGNORE':
                        tokens.append(token.name)
                        if token.value != None:
                            tokens.append(match.group(token.value))

                    content = content[len(match.group(0)):]
                    matched = True
                    break


    token_defs = [
        # Keywords
        Token('ASSIGN'      , 'LET'            ),
        Token('PRINT'       , 'PRINT'          ),
        Token('INPUT'       , 'INPUT'          ),
        Token('EQUALS'      , 'EQ'             ),
        Token('GREATER'     , 'GR'             ),
        Token('GREATERTHEN' , 'GT'             ),
        Token('CALL'        , 'CALL'           ),
        Token('CONCAT'      , 'CONCAT'         ),
        Token('DEF'         , 'DEF'            ),
        Token('SUM'         , 'SUM'            ),
        Token('SUB'         , 'SUB'            ),
        Token('IF'          , 'IF'             ),
        Token('RETURN'      , 'RET'            ),
        Token('EXPORT'      , 'EXPR'           ),
        Token('IMPORT'      , 'IMPRT'          ),
        Token('WHILE'       , 'WHILE'          ),
        Token('AND'         , 'AND'            ),
        Token('OR'          , 'OR'             ),
        Token('NOT'         , 'NOT'            ),
        Token('LOAD'        , 'LOAD'           ),
        Token('CODE'        , 'CODE'           ),
        Token('EXEC'        , 'EXEC'           ),
        Token('LBRAC'       , '\\('            ),
        Token('RBRAC'       , '\\)'            ),
        Token('START_BLOCK' , '\\{'            ),
        Token('END_BLOCK'   , '\\}'            ),
        Token('IGNORE'      , '([ \n]+|# .*\n)'),

        # Token with values
        Token('STRING'      , '"([^"]*)"'             , 1),
        Token('NUMBER'      , '[0-9]+'                , 0),
        Token('NAME'        , '[a-zA-Z][a-zA-Z0-9_]*' , 0),
    ]

    tokens = ['START_BLOCK']

    tokenize(token_defs, content)

    tokens.append('END_BLOCK')

    return tokens

def syntactic_tree(tokens):
    """ Create execution tree from stream of tokens """

    def build_multiple(count):
        result = []
        for i in range(0, count):
            result.append(build_branch(tokens.pop(0)))
        return result
    
    def build_wargs(token, count):
        return {
            'type' : token,
            'args' : build_multiple(count),
        }
    
    def build_value(token):
        return {
            'type' : token,
            'value' : tokens.pop(0),
        }
    
    def build_block():
        exprs = []
        while tokens[0] != 'END_BLOCK':
            res = build_branch(tokens.pop(0))
            if res != None:
                exprs.append(res)
        tokens.pop(0)
        return {
            'type' : 'BLOCK',
            'exprs' : exprs
        }
    
    def build_def():
        tokens.pop(0)
        func_name = tokens.pop(0)
        func_args = []
        while tokens.pop(0) == 'NAME':
            func_args.append(tokens.pop(0))
        functions[func_name] = {
            'args' : func_args,
            'body' : build_block()
        }
    
    def build_call():
        tokens.pop(0)
        func_name = tokens.pop(0)
        tokens.pop(0)
        params = []
        while tokens[0] != 'RBRAC':
            params.append(build_branch(tokens.pop(0)))
        tokens.pop(0)
        return {
            'type' : 'CALL',
            'func_name' : func_name,
            'params' : params
        }
            

    def build_branch(token):
        if token == 'ASSIGN'        : return build_wargs(token, 2)
        elif token == 'SUM'         : return build_wargs(token, 2)
        elif token == 'SUB'         : return build_wargs(token, 2)
        elif token == 'AND'         : return build_wargs(token, 2)
        elif token == 'OR'          : return build_wargs(token, 2)
        elif token == 'PRINT'       : return build_wargs(token, 1)
        elif token == 'CONCAT'      : return build_wargs(token, 2)
        elif token == 'NUMBER'      : return build_value(token)
        elif token == 'INPUT'       : return build_wargs(token, 1)
        elif token == 'START_BLOCK' : return build_block()
        elif token == 'NAME'        : return build_value(token)
        elif token == 'STRING'      : return build_value(token)
        elif token == 'EXPORT'      : return build_wargs(token, 1)
        elif token == 'IMPORT'      : return build_wargs(token, 1)
        elif token == 'RETURN'      : return build_wargs(token, 1)
        elif token == 'IF'          : return build_wargs(token, 3)
        elif token == 'NOT'         : return build_wargs(token, 1)
        elif token == 'WHILE'       : return build_wargs(token, 2)
        elif token == 'EQUALS'      : return build_wargs(token, 2)
        elif token == 'GREATER'     : return build_wargs(token, 2)
        elif token == 'GREATERTHEN' : return build_wargs(token, 2)
        elif token == 'DEF'         : build_def()
        elif token == 'CALL'        : return build_call()
        elif token == 'CODE'        : return build_wargs(token, 1)
        elif token == 'EXEC'        : return build_wargs(token, 1)
        elif token == 'LOAD'        : return build_wargs(token, 1)
        else: print('UNKNOWN', token)
    
    return build_branch(tokens.pop(0))

def interpret(tree, loca_vars):
    """ Execute syntactic tree with predefined local_vars """
    def eval_list(exprs):
        res = []
        for expr in exprs:
            res.append(eval_expr(expr))
        return res

    def eval_math(function, args):
        args = eval_list(args)
        return {
            'type' : 'NUMBER',
            'value' : function(int(args[0]['value']), int(args[1]['value']))
        }
    
    def eval_sum(expr): return eval_math(lambda a, b: a + b, expr['args'])
    def eval_sub(expr): return eval_math(lambda a, b: a - b, expr['args'])

    def eval_block(expr):
        for stat in expr['exprs']:
            if stat['type'] == 'RETURN':
                return eval_expr(stat['args'][0])
            else: eval_expr(stat)
    
    def eval_concat(expr):
        args = eval_list(expr['args'])
        return {
            'type' : 'STRING',
            'value' : str(args[0]['value']) + str(args[1]['value'])
        }
    
    def eval_assign(expr):
        var_name = expr['args'][0]['value']
        loca_vars[var_name] = eval_expr(expr['args'][1])
    
    def eval_print(expr):
        print(eval_expr(expr['args'][0])['value'])
    
    def eval_get(expr):
        return loca_vars[expr['value']]
    
    def eval_call(expr):
        func_name = expr['func_name']
        args = functions[func_name]['args']
        local = {}
        i = 0
        for arg in args:
            local[arg] = expr['params'][i]
            i += 1

        return interpret(
            functions[func_name]['body'],
            local
        )
    
    def true(expr):
        if expr['value'] in [None, "0", 0]:
            return False
        else: return True

    def eval_if(expr):
        condition = eval_expr(expr['args'][0])
        
        if true(condition):
            return eval_expr(expr['args'][1])
        else: return eval_expr(expr['args'][2])
    
    def return_logic(condition):
        if condition:
            return {
                'type' : 'NUMBER',
                'value' : "1"
            }
        else: return {
                'type' : 'NUMBER',
                'value' : "0"
            }

    def eval_equals(expr):
        args = eval_list(expr['args'])

        return return_logic(
            str(args[0]['value']) == str(args[1]['value'])
        )

    def eval_cmp(function, args):
        args = eval_list(args)

        return return_logic(
            function(int(args[0]['value']), int(args[1]['value']))
        )

    def eval_greater(expr): return eval_cmp(lambda a,b: a > b, expr['args'])
    def eval_greaterthen(expr): return eval_cmp(lambda a,b: a >= b, expr['args'])

    def eval_logic(expr, args):
        args = eval_list(args)

        return return_logic(
            function(true(args[0]), true(args[1]))
        )

    def eval_and(expr): return eval_logic(lambda a,b: a and b, expr['args'])
    def eval_or(expr): return eval_logic(lambda a,b: a or b, expr['args'])
    
    def eval_not(expr):
        arg = eval_expr(expr['args'][0])

        return return_logic(not true(arg))
    
    def eval_load(expr):
        load(expr['args'][0]['value'])
    
    def eval_export(expr):
        name = expr['args'][0]['value']
        globvar[name] = loca_vars[name]
    
    def eval_import(expr):
        name = expr['args'][0]['value']
        loca_vars[name] = globvars[name]
    
    def eval_value(expr):
        return eval_expr(expr['args'][0])
    
    def eval_input(expr):
        loca_vars[expr['args'][0]['value']] = {
            'type' : 'STRING',
            'value' : input()
        }
    
    def eval_exec(expr):
        code = eval_expr(expr['args'][0])
        return eval_expr(code['args'][0])
    
    def eval_while(expr):
        while true(eval_expr(expr['args'][0])):
            eval_expr(expr['args'][1])


    def eval_expr(expr):
        if expr['type'] == 'BLOCK'         : return eval_block(expr)
        elif expr['type'] == 'SUM'         : return eval_sum(expr)
        elif expr['type'] == 'SUB'         : return eval_sub(expr)
        elif expr['type'] == 'ASSIGN'      : return eval_assign(expr)
        elif expr['type'] == 'NAME'        : return eval_get(expr)
        elif expr['type'] == 'CALL'        : return eval_call(expr)
        elif expr['type'] == 'CONCAT'      : return eval_concat(expr)
        elif expr['type'] == 'LOAD'        : return eval_load(expr)
        elif expr['type'] == 'PRINT'       : return eval_print(expr)
        elif expr['type'] == 'IF'          : return eval_if(expr)
        elif expr['type'] == 'IMPORT'      : return eval_import(expr)
        elif expr['type'] == 'EXPORT'      : return eval_export(expr)
        elif expr['type'] == 'INPUT'       : return eval_input(expr)
        elif expr['type'] == 'EQUALS'      : return eval_equals(expr)
        elif expr['type'] == 'GREATER'     : return eval_greater(expr)
        elif expr['type'] == 'GREATERTHEN' : return eval_greaterthen(expr)
        elif expr['type'] == 'AND'         : return eval_and(expr)
        elif expr['type'] == 'OR'          : return eval_or(expr)
        elif expr['type'] == 'NOT'         : return eval_not(expr)
        elif expr['type'] == 'EXEC'        : return eval_exec(expr)
        elif expr['type'] == 'WHILE'       : eval_while(expr)
        else: return expr
    
    return eval_expr(tree)

def load(path):
    """ Load file, add function and definitions, execute main """
    content = open(path).read()
    tokens = lexical_analisys(content)
    tree = syntactic_tree(tokens)
    interpret(tree, {})

load(path)
