#!/usr/bin/python3
from sys import argv
from collections import namedtuple, defaultdict
from re import compile
from ntpath import basename
from pprint import pprint

INDENT_SIZE = 4
EXTENSION_SIZE = 4

"""
Experimental programming language 2 

"""

path = argv[1]
scobe = ['START']
functions = {}
globvars = {}

def lexical_analisys(content):

    class Token:
        """ Class representing one token """
        def __init__(self, name, pattern, value = None):
            self.name = name
            self.pattern = compile(pattern)
            self.value = value
        def match(self, content): return self.pattern.match(content)
    

    def escape(token, match):
        """ We are in unescaped string """
        tokens.append(token.name)
        if token.name == 'STAT':
            tokenize(token_defs, match.group(1), statement)
        else:
            tokens.append(match.group(0))
    
    def term(token, match):
        """ We are in the term """
        tokens.append(token.name)
        if token.name == 'NAME':
            tokens.append(match.group(token.value))
    
    def statement(token, match):
        """ Classis statement, probably in infix """
        if token.name == 'INDENT':

            act_indent = int(len(match.group(0))/4)

            while act_indent > statement.indentation:
                statement.indentation += 1
                tokens.append('START_BLOCK')

            while act_indent < statement.indentation:
                statement.indentation -= 1
                tokens.append('END_BLOCK')

        elif token.name == 'UNESC_STRING':
            tokens.append(token.name)
            tokenize(escape_token_defs, match.group(1), escape)
        elif token.name == 'TERM':
            tokens.append(token.name)
            tokenize(term_token_defs, match.group(0), term)
        elif token.name != 'IGNORE':
            tokens.append(token.name)
            if token.value != None:
                tokens.append(match.group(token.value))

    statement.indentation = 0

                        
        
    def tokenize(token_defs, content, context):

        matched = True

        while len(content) > 0:
        
            if not matched:
                print("UNMATCHED CONTENT\n", content)
                break
            else: matched = False

            for token in token_defs:
                match = token.match(content)
                if match: 
                    context(token, match)
                    content = content[len(match.group(0)):]
                    matched = True
                    break


    escape_token_defs = [
        Token('TEXT', '([^$\\\\]|(\\\\\$|\\\\))+'),
        Token('STAT', '\\$([^ $]+)') # Single word statement
    ]

    term_token_defs = [
        Token('DELIMITER', '\\\\'),
        Token('NAME'   , '[a-zA-Z][a-zA-Z0-9_]*'       , 0),
    ]

    token_defs = [
        # Operands
        Token('EQUALS'      , '=='             ),
        Token('GREATERTHEN' , '>='             ),
        Token('AND'         , '&&'             ),
        Token('OR'          , '\\|\\|'         ),
        Token('ASSIGN'      , '='              ),
        Token('GREATER'     , '>'              ),
        Token('SUM'         , '\\+'            ),
        Token('MUL'         , '\\*'            ),
        Token('SUB'         , '-'              ),
        Token('SQR'         , '\\^'            ), #TODO Not implemented in parser
        Token('CONCAT'      , '\\$'            ),
        
        # Keywords
        Token('IF'          , '(\\?|if|IF)'    ), # If statement
        Token('ELSE'        , '(else|ELSE|\\:)'), # Else for if
        Token('DEF'         , '(def|DEF)'      ), # Define function
        Token('PRINT'       , '(print|PRINT)'  ), # Print result of next stat
        Token('ILN'         , 'ILN'            ), # Return line from input
        Token('INPUT'       , '(input|INPUT)'  ), # Assign input to variable
        Token('RETURN'      , '(ret|RET)'      ), # Return result of block
        Token('WHILE'       , '(while|WHILE)'  ), # While cycle
        Token('NOT'         , '(not|NOT|\\!)'  ), # Negation
        Token('LOAD'        , '(load|LOAD)'    ), # Load file
        Token('CODE'        , '(code|CODE)'    ), # Return statement without eval
        Token('EXEC'        , '(exec|EXEC)'    ), # Execute code in variable
        Token('LBRAC'       , '\\('            ),
        Token('RBRAC'       , '\\)'            ),

        # Ignored tokens
        Token('IGNORE'      , '#\\{[^\\}]*\\}'    ), # Multiline comment
        Token('IGNORE'      , '(#[^\n]*\n)'       ), # Single line comment

        # Indent, must by behind one liner comment, to not indednting them
        Token('INDENT'      , '\n(( {4})*)'  ),

        # Ignore spaces, must by behind indent
        Token('IGNORE'      , ' +'),

        # Tokens with values
        Token('STRING' , "'(([^']*(\\\\')?)*[^\\\\])'" , 1),
        Token('NUMBER' , '(0|[1-9][0-9]*)'             , 0),
        Token('TERM'   , '[a-zA-Z0-9_\\\\]+'           , 0),

        # Tokens that are scanned
        Token('UNESC_STRING' , '"(([^"]*(\\\\")?)*[^\\\\])"' , 1),
    ]

    tokens = ['START_BLOCK'] # Initial block of code

    tokenize(token_defs, content, statement)

    tokens.append('END_BLOCK')

    return tokens

def build_tree(tokens):
    """ Build execution tree for interpreter """
    def prec(name):
        if name in ['SQR']: return 90
        elif name in ['MUL', 'DIV']: return 80
        elif name in ['SUM', 'SUB', 'CONCAT']: return 70
        elif name in ['EQUALS', 'GREATHER']: return 60
        elif name in ['AND', 'OR']: return 50
        elif name in ['ASSIGN']: return 40
        else: return 0
    
    def mpop(collection, count):
        while count > 0:
            collection.pop(0)
            count -= 1
        return collection.pop(0)

    def build_multiple(count):
        result = []
        for i in range(0, count):
            result.append(build_branch())
        return result
    
    def build_wargs(token, count):
        return {
            'type' : token,
            'args' : build_multiple(count)
        }
    
    def build_block(token):
        value = []
        while tokens[0] != 'END_BLOCK':
            res = build_branch()
            if res != None:
                value.append(res)

        tokens.pop(0)
        return {
            'type' : 'BLOCK',
            'value' : value
        }
        
    def build_value(token):
        return {
            'type' : token,
            'value' : tokens.pop(0)
        }

    def build_def(token):
        # TODO Nasty hack, need to do it some other way
        # it is problem resolve it term is term, or func name
        args = []
        name = mpop(tokens, 2)
        while tokens[0] == 'TERM': 
            args.append(mpop(tokens, 2))

        functions[name] = {
            'args' : args,
            'body' : build_branch()
        }
    
    def build_call(name):
        tok = {'type' : 'CALL', 'name' : name, 'params' : {}}
        for arg in functions[tok['name']]['args']:
            tok['params'][arg] = build_branch()
        return tok
    
    def build_if(token):
        tok = {
            'type' : token, 
            'cond' : build_branch(),
            'true' : build_branch(),
            'false' : None
        }
        if tokens[0] == 'ELSE': 
            tokens.pop(0)
            tok['false'] = build_branch()
        return tok
    
    def build_term(token):
        """ Resolving namespacing """
        names = []

        if tokens[0] == 'DELIMITER': typ = 'G_NAME'
        else: typ = 'L_NAME'

        while tokens[0] in ['NAME', 'DELIMITER']: 
            if tokens.pop(0) == 'NAME':
                names.append(tokens.pop(0))

        if len(names) > 1:
            name = '\\'.join(names)
            typ = 'G_NAME'
        elif typ == 'G_NAME':
            name = '\\'.join(scobe) + '\\' + names[0]
        else: name = names[0]
            

        if name in functions:
            return build_call(name)
        else:
            return {
                'type' : typ ,
                'value' : name
            }
    
    def build_load(token):
        return {
            'type' : token,
            'body' : load(build_param(tokens.pop(0))['value'])
        }
    
    def build_unescaped_string(token):
        body = []
        while tokens[0] in ['TEXT', 'STAT']:
            tok = tokens.pop(0)
            if tok == 'TEXT':
                body.append({
                    'type' : 'TEXT',
                    'value' : tokens.pop(0)
                })
            elif tok == 'STAT':
                body.append({
                    'type' : 'STAT',
                    'value' : build_branch()
                })
        return {
            'type' : token,
            'body' : body
        }


    def build_param(token):
        if token in ['STRING', 'NUMBER', 'NAME']:
            return build_value(token)
        elif token in [
            'PRINT', 'EXPORT', 'IMPORT',
            'RETURN','NOT','CODE', 'INPUT',
            'EXEC']     : return build_wargs(token, 1)
        elif token == 'TERM'        : return build_term(token)
        elif token == 'START_BLOCK' : return build_block(token)
        elif token == 'IF'          : return build_if(token)
        elif token == 'WHILE'       : return build_wargs(token, 2)
        elif token == 'DEF'         : return build_def(token)
        elif token == 'LOAD'        : return build_load(token)
        elif token == 'UNESC_STRING': return build_unescaped_string(token)
        elif token == 'ILN'         : return {'type' : 'ILN'}
        else: print('UNKNOWN TOKEN', token)

    operands = [
        'EQUALS', 'SUM', 'ASSIGN', 'MUL', 'CONCAT', 'SUB', 'GREATER'
    ]

    brac = [
        'LBRAC',  'RBRAV'
    ]

    no_param = operands + brac

    def build_branch():
        
        stack = []
        expression = []
        
        def build_infix(token):
            if token in operands:
                arg2 = build_infix(expression.pop(-1))
                arg1 = build_infix(expression.pop(-1))
                return {
                    'type' : token,
                    'args' : [
                        arg1,
                        arg2
                    ]
                }
            else: return token

        i = 0
        brackets = 0

        while len(tokens) > 0:
            if tokens[0] in operands and i%2 == 1:
                act_prec = prec(tokens[0])
                while len(stack) > 0 and prec(stack[-1]) >= act_prec:
                    expression.append(stack.pop())
                stack.append(tokens.pop(0))
            elif tokens[0] == 'LBRAC' and i%2 == 0:
                i = 1
                brackets += 1
                stack.append(tokens.pop(0))
            elif tokens[0] == 'RBRAC' and i%2 == 1 and brackets > 0:
                i = 0
                brackets -= 1
                tokens.pop(0)
                while stack[-1] != 'LBRAC':
                    expression.append(stack.pop())
                stack.pop()
            elif i%2 == 0 and tokens[0] not in no_param:
                expression.append(build_param(tokens.pop(0)))
            else:
                break
            i += 1

        while len(stack) > 0:
            expression.append(stack.pop())

        return build_infix(expression.pop(-1))
    
    return build_block(tokens.pop(0))

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
    def eval_mul(expr): return eval_math(lambda a, b: a * b, expr['args'])

    def eval_block(expr):
        for stat in expr['value']:
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
        var_type = expr['args'][0]['type']
        value = eval_expr(expr['args'][1])
        if var_type == 'L_NAME':
            loca_vars[var_name] = eval_expr(value)
        elif var_type == 'G_NAME':
            globvars[var_name] = eval_expr(value)
        return value
    
    def eval_print(expr):
        print(eval_expr(expr['args'][0])['value'])
    
    def eval_lget(expr): return loca_vars[expr['value']]
    def eval_gget(expr): 
        return globvars[expr['value']]

    
    def eval_call(expr):
        func_name = expr['name']

        return interpret(
            functions[func_name]['body'],
            expr['params']
        )
    
    def true(expr):
        if expr['value'] in [None, "0", 0]:
            return False
        else: return True

    def eval_if(expr):
        condition = eval_expr(expr['cond'])
        
        if true(condition):
            return eval_expr(expr['true'])
        elif expr['false'] != None:
            return eval_expr(expr['false'])
    
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
        interpret(expr['body'], {})
    
    def eval_export(expr):
        name = expr['args'][0]['value']
        globvar[name] = loca_vars[name]
    
    def eval_import(expr):
        name = expr['args'][0]['value']
        loca_vars[name] = globvars[name]
    
    def eval_value(expr):
        return eval_expr(expr['args'][0])
    
    def eval_iln(expr):
        return {
            'type' : 'STRING',
            'value' : input()
        }
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
    
    def eval_unescaped_string(expr):
        
        ret = ''
        
        for piece in expr['body']:
            if piece['type'] == 'TEXT':
                ret += piece['value']
            else:
                ret += eval_expr(piece['value'])['value']

        return {
            'type' : 'STRING',
            'value' : ret
        }

    def eval_expr(expr):
        if expr['type'] == 'BLOCK'         : return eval_block(expr)
        elif expr['type'] == 'SUM'         : return eval_sum(expr)
        elif expr['type'] == 'SUB'         : return eval_sub(expr)
        elif expr['type'] == 'MUL'         : return eval_mul(expr)
        elif expr['type'] == 'ASSIGN'      : return eval_assign(expr)
        elif expr['type'] == 'L_NAME'      : return eval_lget(expr)
        elif expr['type'] == 'G_NAME'      : return eval_gget(expr)
        elif expr['type'] == 'CALL'        : return eval_call(expr)
        elif expr['type'] == 'CONCAT'      : return eval_concat(expr)
        elif expr['type'] == 'LOAD'        : return eval_load(expr)
        elif expr['type'] == 'PRINT'       : return eval_print(expr)
        elif expr['type'] == 'IF'          : return eval_if(expr)
        elif expr['type'] == 'IMPORT'      : return eval_import(expr)
        elif expr['type'] == 'EXPORT'      : return eval_export(expr)
        elif expr['type'] == 'ILN'         : return eval_iln(expr)
        elif expr['type'] == 'INPUT'       : return eval_input(expr)
        elif expr['type'] == 'EQUALS'      : return eval_equals(expr)
        elif expr['type'] == 'GREATER'     : return eval_greater(expr)
        elif expr['type'] == 'GREATERTHEN' : return eval_greaterthen(expr)
        elif expr['type'] == 'AND'         : return eval_and(expr)
        elif expr['type'] == 'OR'          : return eval_or(expr)
        elif expr['type'] == 'NOT'         : return eval_not(expr)
        elif expr['type'] == 'EXEC'        : return eval_exec(expr)
        elif expr['type'] == 'UNESC_STRING': return eval_unescaped_string(expr)
        elif expr['type'] == 'WHILE'       : eval_while(expr)
        else: return expr
    
    return eval_expr(tree)

def load(path):
    """ Load file, add function and definitions, execute main """
    scobe.pop()
    scobe.append(path[0:-EXTENSION_SIZE].replace('/', '\\'))
    content = open(path).read() + "\n"
    tokens = lexical_analisys(content)
    return build_tree(tokens)

tree = load(path)
interpret(tree, {})
