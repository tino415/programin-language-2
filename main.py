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

fil = argv[1]
functions = {}
globvars = {}

def lexical_analisys(content):

    class Token:
        def __init__(self, name, pattern, value = None, clear = 0):
            self.name = name
            self.pattern = compile(pattern)
            self.value = value
            self.clear = 0
        def match(self, content): return self.pattern.match(content)
    
    def tokenize(token_defs, content):
        while len(content) > 0:
            for token in token_defs:
                match = token.match(content)
                if match:
                    if token.name != 'IGNORE':
                        tokens.append(token.name)
                        if token.value != None:
                            tokens.append(match.group(token.value))

                    content = content[len(match.group(token.clear)):]
                    break


    token_defs = [
        Token('ASSIGN', 'LET'),
        Token('PRINT', 'PRINT'),
        Token('INPUT', 'INPUT'),
        Token('EQUALS', 'EQ'),
        Token('CALL' , 'CALL'),
        Token('CONCAT', 'CONCAT'),
        Token('DEF', 'DEF'),
        Token('SUM', 'SUM'),
        Token('IF', 'IF'),
        Token('RETURN', 'RET'),
        Token('EXPORT', 'EXPR'),
        Token('IMPORT', 'IMPRT'),
        Token('WHILE', 'WHILE'),
        Token('AND', 'AND'),
        Token('OR', 'OR'),
        Token('NOT', 'NOT'),
        Token('LOAD', 'LOAD'),
        Token('LBRAC', '\('),
        Token('RBRAC', '\)'),
        Token('STRING', '"([^"]*)"', 1),
        Token('IGNORE', '([ \n]+|# .*\n)'),
        Token('START_BLOCK', '\\{'),
        Token('END_BLOCK', '\\}'),
        Token('NUMBER', '[0-9]+', 0),
        Token('NAME', '[a-zA-Z][a-zA-Z0-9_]*', 0),
    ]

    tokens = ['START_BLOCK']

    tokenize(token_defs, content)

    tokens.append('END_BLOCK')

    return tokens

def syntactic_tree(tokens):
    
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
        if token == 'ASSIGN': return build_wargs(token,2)
        elif token == 'SUM' : return build_wargs(token,2)
        elif token == 'AND' : return build_wargs(token,2)
        elif token == 'OR' : return build_wargs(token,2)
        elif token == 'PRINT': return build_wargs(token,1)
        elif token == 'CONCAT': return build_wargs(token, 2)
        elif token == 'NUMBER': return build_value(token)
        elif token == 'INPUT': return build_wargs(token, 1)
        elif token == 'START_BLOCK': return build_block()
        elif token == 'NAME': return build_value(token)
        elif token == 'STRING' : return build_value(token)
        elif token == 'EXPORT' : return build_wargs(token, 1)
        elif token == 'IMPORT' : return build_wargs(token, 1)
        elif token == 'RETURN' : return build_wargs(token, 1)
        elif token == 'IF' : return build_wargs(token, 3)
        elif token == 'NOT' : return build_wargs(token, 1)
        elif token == 'WHILE' : return build_wargs(token, 2)
        elif token == 'EQUALS' : return build_wargs(token, 2)
        elif token == 'DEF' : build_def()
        elif token == 'CALL' : return build_call()
        elif token == 'LOAD' : return build_wargs(token, 1)
        else: print('UNKNOWN', token)
    
    return build_branch(tokens.pop(0))

def parse(tree, loca_vars):

    def eval_list(exprs):
        res = []
        for expr in exprs:
            res.append(eval_expr(expr))
        return res
    
    def eval_block(expr):
        for stat in expr['exprs']:
            if stat['type'] == 'RETURN':
                return eval_expr(stat['args'][0])
            else: eval_expr(stat)

    def eval_sum(expr):
        args = eval_list(expr['args'])
        return {
            'type' : 'NUMBER',
            'value' : int(args[0]['value']) + int(args[1]['value'])
        }
    
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
            func_name,
            local
        )
    
    def eval_if(expr):
        condition = eval_expr(expr['args'][0])
        
        if condition['value'] not in [None, "0", 0]:
            return eval_expr(expr['args'][1])
        else: return eval_expr(expr['args'][2])
    
    def true(expr):
        if expr['value'] in [None, "0", 0]:
            return False
        else: return True


    def eval_equals(expr):
        args = eval_list(expr['args'])

        if str(args[0]['value']) == str(args[1]['value']):
            return {
                'type' : 'NUMBER',
                'value' : "1"
            }
        else: return {
                'type' : 'NUMBER',
                'value' : "0"
            }

    def eval_and(expr):
        args = eval_list(expr['args'])

        if true(args[0]) and true(args[1]):
            return {
                'type' : 'NUMBER',
                'value' : "1"
            }
        else: return {
                'type' : 'NUMBER',
                'value' : "0"
            }

    def eval_or(expr):
        args = eval_list(expr['args'])

        if true(args[0]) or true(args[1]):
            return {
                'type' : 'NUMBER',
                'value' : "1"
            }
        else: return {
                'type' : 'NUMBER',
                'value' : "0"
            }
    
    def eval_not(expr):
        arg = eval_expr(expr['args'][0])

        if true(arg):
            return {
                'type' : 'NUMBER',
                'value' : "0"
            }
        else: return {
            'type' : 'NUMBER',
            'value' : "1"
        }
    
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
    
    def eval_while(expr):
        while true(eval_expr(expr['args'][0])):
            eval_expr(expr['args'][1])


    def eval_expr(expr):
        if expr['type'] == 'BLOCK': return eval_block(expr)
        elif expr['type'] == 'SUM': return eval_sum(expr)
        elif expr['type'] == 'ASSIGN' : return eval_assign(expr)
        elif expr['type'] == 'NAME' : return eval_get(expr)
        elif expr['type'] == 'CALL' : return eval_call(expr)
        elif expr['type'] == 'CONCAT' : return eval_concat(expr)
        elif expr['type'] == 'LOAD' : return eval_load(expr)
        elif expr['type'] == 'PRINT' : return eval_print(expr)
        elif expr['type'] == 'IF' : return eval_if(expr)
        elif expr['type'] == 'IMPORT' : return eval_import(expr)
        elif expr['type'] == 'EXPORT' : return eval_export(expr)
        elif expr['type'] == 'INPUT' : return eval_input(expr)
        elif expr['type'] == 'EQUALS' : return eval_equals(expr)
        elif expr['type'] == 'AND' : return eval_and(expr)
        elif expr['type'] == 'OR' : return eval_or(expr)
        elif expr['type'] == 'NOT' : return eval_not(expr)
        elif expr['type'] == 'WHILE' : eval_while(expr)
        else: return expr
    
    return eval_expr(tree)

def interpret(func_name, params):
    
    return parse(functions[func_name]['body'], params)

def load(path):
    
    content = open(path).read()
    tokens = lexical_analisys(content)
    tree = syntactic_tree(tokens)
    parse(tree, {})

load(fil)
