
#######################################
# IMPORTS
#######################################

import sys
from typing import Text
from arrows import *
import string
from SymbolTable import *
sys.path.insert(0, "../..")




####################################################################################
##                      LEXER CODE TOKENS AND EXTRA CODE
####################################################################################



#TOKENS
#I will separate these tokens into stages of programming, so it is easy to follow when 
#a variable or token was added into the code.
#1st stage
TT_INT = 'INT'
TT_FLOAT = 'FLOAT'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'

#2nd stage
TT_EOF = 'EOF'
TT_EXPONENT = 'EXPONENT'

#3rd stage
TT_ID = 'ID'
TT_KEYWORD = 'KEYWORD'
TT_EQ = 'EQ'

#4th stage
TT_EXACT = 'EXACT'
TT_NE = 'NOTEQUALS'
TT_LT = 'LESSTHAN'
TT_GT = 'GREATERTHAN'
TT_LTE = 'LESSTHANEQUALS'
TT_GTE = 'GREATERTHANEQUALS'

#8th stage
TT_COMMA = 'COMMA'
TT_ARROW = 'ARROW'


END = 'END'


VARLIST = [
    'VAR', #3RD
    'AND', #4th
    'OR',  #4th
    'NOT', #4th
    'IF',  #5th
    'THEN',#5th
    'ELIF',#5th
    'ELSE',#5th
    'FOR', #6th
    'TO',  #6th
    'STEP', #6th
    'WHILE', #7th
    'FUN' #8th

]

#CONSTANTS
DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS


# ERRORS
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
    
    def as_string(self):
        errorLog  = f'{self.error_name}: {self.details}\n'
        errorLog += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        errorLog += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return errorLog

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    def as_string(self):
        errorLog  = self.generate_traceback()
        errorLog += f'{self.error_name}: {self.details}'
        errorLog += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return errorLog

    def generate_traceback(self):
        errorLog = ''
        pos = self.pos_start
        ctx = self.context

        while ctx:
            errorLog = f'  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + errorLog
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return 'Traceback (most recent call last):\n' + errorLog


# POSITION
class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


#TOKEN CLASS to generate tokens
class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value
    
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'


# LEXER CODE
class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:

            if self.current_char in ' \t':
                self.advance()

            elif self.current_char in DIGITS:
                tokens.append(self.make_num())

            elif self.current_char in LETTERS:
                tokens.append(self.make_id())

            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()

            elif self.current_char == '-':
                tokens.append(self.make_minus_or_arrow())

            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()

            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()

            elif self.current_char == '^':
                tokens.append(Token(TT_EXPONENT, pos_start=self.pos))
                self.advance()

            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()

            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()

            elif self.current_char == '!':
                token, error = self.make_notEquals()
                if error: return [], error
                tokens.append(token)

            elif self.current_char == '=':
                tokens.append(self.make_equals())

            elif self.current_char == '<':
                tokens.append(self.make_lessThan())

            elif self.current_char == '>':
                tokens.append(self.make_greaterThan())

            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()

            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_num(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()
        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    def make_id(self):
        id_str = ''
        pos_start = self.pos.copy()
        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()
        tok_type = TT_KEYWORD if id_str in VARLIST else TT_ID
        return Token(tok_type, id_str, pos_start, self.pos)

    def make_minus_or_arrow(self):
        tok_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '>':
            self.advance()
            tok_type = TT_ARROW
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_notEquals(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None
        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")
    
    def make_equals(self):
        tok_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            tok_type = TT_EQ
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_lessThan(self):
        tok_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            tok_type = TT_LTE
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_greaterThan(self):
        tok_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            tok_type = TT_GTE
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)



##############################################################################################################
##                      START OF PARSER CODE
##############################################################################################################


# NODES
class NumberNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'

class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end

class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'

class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node
        self.pos_start = self.op_tok.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'

class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case
        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[len(self.cases) - 1][0]).pos_end

class ForNode:
    def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node):
        self.var_name_tok = var_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.body_node.pos_end

class WhileNode:
    def __init__(self, condition_node, body_node):
        self.condition_node = condition_node
        self.body_node = body_node
        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end

class FuncDefNode:
    def __init__(self, var_name_tok, arg_name_toks, body_node):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        if self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start
        self.pos_end = self.body_node.pos_end

class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end



# PARSE RESULT
class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0

    def register_advancement(self):
        self.last_registered_advance_count = 1
        self.advance_count += 1

    def register(self, response):
        self.last_registered_advance_count = response.advance_count
        self.advance_count += response.advance_count
        if response.error: self.error = response.error
        return response.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
        return self


# PARSERCODE
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self, ):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def parse(self):
        response = self.expr()
        if not response.error and self.current_tok.type != TT_EOF:
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'AND' or 'OR'"))
        return response


# Defenitions for each different type of expression, based on recursion. AKA GRAMMAR RULES
    def expr(self):
        response = ParseResult()
        if self.current_tok.matches(TT_KEYWORD, 'VAR'):
            response.register_advancement()
            self.advance()
            if self.current_tok.type != TT_ID:
                return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier"))

            var_name = self.current_tok
            response.register_advancement()
            self.advance()
            if self.current_tok.type != TT_EQ:
                return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '='"))

            response.register_advancement()
            self.advance()
            expr = response.register(self.expr())
            if response.error: return response
            return response.success(VarAssignNode(var_name, expr))

        node = response.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, 'AND'), (TT_KEYWORD, 'OR'))))
        if response.error:
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(' or 'NOT'"))

        return response.success(node)


    def comp_expr(self):
        response = ParseResult()
        if self.current_tok.matches(TT_KEYWORD, 'NOT'):
            op_tok = self.current_tok
            response.register_advancement()
            self.advance()
            node = response.register(self.comp_expr())
            if response.error: return response
            return response.success(UnaryOpNode(op_tok, node))
        
        node = response.register(self.bin_op(self.arith_expr, (TT_EQ, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))
        if response.error: return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected int, float, identifier, '+', '-', '(' or 'NOT'"))
        return response.success(node)


    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))


    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))


    def factor(self):
        response = ParseResult()
        tok = self.current_tok
        if tok.type in (TT_PLUS, TT_MINUS):
            response.register_advancement()
            self.advance()
            factor = response.register(self.factor())
            if response.error: return response
            return response.success(UnaryOpNode(tok, factor))
        return self.power()


    def power(self):
        return self.bin_op(self.call, (TT_EXPONENT, ), self.factor)


    def call(self):
        response = ParseResult()
        atom = response.register(self.atom())
        if response.error: return response

        if self.current_tok.type == TT_LPAREN:
            response.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_tok.type == TT_RPAREN:
                response.register_advancement()
                self.advance()
            else:
                arg_nodes.append(response.register(self.expr()))
                if response.error:
                    return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ')', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(' or 'NOT'"))

                while self.current_tok.type == TT_COMMA:
                    response.register_advancement()
                    self.advance()
                    arg_nodes.append(response.register(self.expr()))
                    if response.error: return response

                if self.current_tok.type != TT_RPAREN:
                    return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected ',' or ')'"))

                response.register_advancement()
                self.advance()
            return response.success(CallNode(atom, arg_nodes))
        return response.success(atom)


    def atom(self):
        response = ParseResult()
        tok = self.current_tok
        if tok.type in (TT_INT, TT_FLOAT):
            response.register_advancement()
            self.advance()
            return response.success(NumberNode(tok))

        elif tok.type == TT_ID:
            response.register_advancement()
            self.advance()
            return response.success(VarAccessNode(tok))

        elif tok.type == TT_LPAREN:
            response.register_advancement()
            self.advance()
            expr = response.register(self.expr())
            if response.error: return response
            if self.current_tok.type == TT_RPAREN:
                response.register_advancement()
                self.advance()
                return response.success(expr)
            else:
                return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ')'"))
        
        elif tok.matches(TT_KEYWORD, 'IF'):
            if_expr = response.register(self.if_expr())
            if response.error: return response
            return response.success(if_expr)

        elif tok.matches(TT_KEYWORD, 'FOR'):
            for_expr = response.register(self.for_expr())
            if response.error: return response
            return response.success(for_expr)

        elif tok.matches(TT_KEYWORD, 'WHILE'):
            while_expr = response.register(self.while_expr())
            if response.error: return response
            return response.success(while_expr)

        elif tok.matches(TT_KEYWORD, 'FUN'):
            func_def = response.register(self.func_def())
            if response.error: return response
            return response.success(func_def)

        return response.failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, "Expected int, float, identifier, '+', '-', '(', 'IF', 'FOR', 'WHILE', 'FUN'"))


    def if_expr(self):
        response = ParseResult()
        cases = []
        else_case = None
        if not self.current_tok.matches(TT_KEYWORD, 'IF'):
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'IF'"))

        response.register_advancement()
        self.advance()
        condition = response.register(self.expr())
        if response.error: return response
        if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'THEN'" ))

        response.register_advancement()
        self.advance()
        expr = response.register(self.expr())
        if response.error: return response
        cases.append((condition, expr))

        while self.current_tok.matches(TT_KEYWORD, 'ELIF'):
            response.register_advancement()
            self.advance()
            condition = response.register(self.expr())
            if response.error: return response
            if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
                return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'THEN'"))

            response.register_advancement()
            self.advance()
            expr = response.register(self.expr())
            if response.error: return response
            cases.append((condition, expr))

        if self.current_tok.matches(TT_KEYWORD, 'ELSE'):
            response.register_advancement()
            self.advance()
            else_case = response.register(self.expr())
            if response.error: return response
        return response.success(IfNode(cases, else_case))


    def for_expr(self):
        response = ParseResult()
        if not self.current_tok.matches(TT_KEYWORD, 'FOR'):
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'FOR'"))

        response.register_advancement()
        self.advance()
        if self.current_tok.type != TT_ID:
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier"))

        var_name = self.current_tok
        response.register_advancement()
        self.advance()
        if self.current_tok.type != TT_EQ:
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected '='"))
        
        response.register_advancement()
        self.advance()
        start_value = response.register(self.expr())
        if response.error: return response

        if not self.current_tok.matches(TT_KEYWORD, 'TO'):
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'TO'"))
        
        response.register_advancement()
        self.advance()
        end_value = response.register(self.expr())
        if response.error: return response

        if self.current_tok.matches(TT_KEYWORD, 'STEP'):
            response.register_advancement()
            self.advance()
            step_value = response.register(self.expr())
            if response.error: return response
        else:
            step_value = None

        if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'THEN'"))

        response.register_advancement()
        self.advance()
        body = response.register(self.expr())
        if response.error: return response
        return response.success(ForNode(var_name, start_value, end_value, step_value, body))


    def while_expr(self):
        response = ParseResult()
        if not self.current_tok.matches(TT_KEYWORD, 'WHILE'):
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'WHILE'"))

        response.register_advancement()
        self.advance()
        condition = response.register(self.expr())
        if response.error: return response
        if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'THEN'"))

        response.register_advancement()
        self.advance()
        body = response.register(self.expr())
        if response.error: return response

        return response.success(WhileNode(condition, body))


    def func_def(self):
        response = ParseResult()
        if not self.current_tok.matches(TT_KEYWORD, 'FUN'):
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'FUN'"))

        response.register_advancement()
        self.advance()
        if self.current_tok.type == TT_ID:
            var_name_tok = self.current_tok
            response.register_advancement()
            self.advance()
            if self.current_tok.type != TT_LPAREN:
                return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected '('"))
        else:
            var_name_tok = None
            if self.current_tok.type != TT_LPAREN:
                return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier or '('"))
        
        response.register_advancement()
        self.advance()
        arg_name_toks = []
        if self.current_tok.type == TT_ID:
            arg_name_toks.append(self.current_tok)
            response.register_advancement()
            self.advance()
            
            while self.current_tok.type == TT_COMMA:
                response.register_advancement()
                self.advance()

                if self.current_tok.type != TT_ID:
                    return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier"))

                arg_name_toks.append(self.current_tok)
                response.register_advancement()
                self.advance()
            
            if self.current_tok.type != TT_RPAREN:
                return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected ',' or ')'"))
        else:
            if self.current_tok.type != TT_RPAREN:
                return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier or ')'"))

        response.register_advancement()
        self.advance()
        if self.current_tok.type != TT_ARROW:
            return response.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected '->'"))

        response.register_advancement()
        self.advance()
        node_to_return = response.register(self.expr())
        if response.error: return response

        return response.success(FuncDefNode(var_name_tok, arg_name_toks, node_to_return))


    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a
        response = ParseResult()
        left = response.register(func_a())
        if response.error: return response

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            response.register_advancement()
            self.advance()
            right = response.register(func_b())
            if response.error: return response
            left = BinOpNode(left, op_tok, right)
        return response.success(left)



##############################################################################################################
##                                  CONTEXT
##############################################################################################################
#Future proofing for function context, add in more code for it once language can hold functions
class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None



##############################################################################################################
##                                  INTERPRETER
##############################################################################################################

#PARSE RESULT
class RTResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, response):
        self.error = response.error
        return response.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self


# NUMBER AND VALUE CLASS
class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def added_to(self, second):
        return None, self.illegal_operation(second)

    def subtracted_by(self, second):
        return None, self.illegal_operation(second)

    def multiplied_by(self, second):
        return None, self.illegal_operation(second)

    def divided_by(self, second):
        return None, self.illegal_operation(second)

    def power_of(self, second):
        return None, self.illegal_operation(second)

    def get_comparison_equals(self, second):
        return None, self.illegal_operation(second)

    def get_comparison_notEquals(self, second):
        return None, self.illegal_operation(second)

    def get_comparison_lessThan(self, second):
        return None, self.illegal_operation(second)

    def get_comparison_greaterThan(self, second):
        return None, self.illegal_operation(second)

    def get_comparison_lessThanEquals(self, second):
        return None, self.illegal_operation(second)

    def get_comparison_greaterThanEquals(self, second):
        return None, self.illegal_operation(second)

    def and_comparedTo(self, second):
        return None, self.illegal_operation(second)

    def or_comparedTo(self, second):
        return None, self.illegal_operation(second)

    def notted(self):
        return None, self.illegal_operation(second)

    def execute(self, args):
        return RTResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception('No copy method defined')

    def is_true(self):
        return False

    def illegal_operation(self, second=None):
        if not second: second = self
        return RTError(
            self.pos_start, second.pos_end,
            'Illegal operation',
            self.context
        )


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, second):
        if isinstance(second, Number):
            return Number(self.value + second.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def subtracted_by(self, second):
        if isinstance(second, Number):
            return Number(self.value - second.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def multiplied_by(self, second):
        if isinstance(second, Number):
            return Number(self.value * second.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def divided_by(self, second):
        if isinstance(second, Number):
            if second.value == 0:
                return None, RTError(second.pos_start, second.pos_end, 'Division by zero', self.context)

            return Number(self.value / second.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def power_of(self, second):
        if isinstance(second, Number):
            return Number(self.value ** second.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def get_comparison_equals(self, second):
        if isinstance(second, Number):
            return Number(int(self.value == second.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def get_comparison_notEquals(self, second):
        if isinstance(second, Number):
            return Number(int(self.value != second.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def get_comparison_lessThan(self, second):
        if isinstance(second, Number):
            return Number(int(self.value < second.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def get_comparison_greaterThan(self, second):
        if isinstance(second, Number):
            return Number(int(self.value > second.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def get_comparison_lessThanEquals(self, second):
        if isinstance(second, Number):
            return Number(int(self.value <= second.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def get_comparison_greaterThanEquals(self, second):
        if isinstance(second, Number):
            return Number(int(self.value >= second.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def and_comparedTo(self, second):
        if isinstance(second, Number):
            return Number(int(self.value and second.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def or_comparedTo(self, second):
        if isinstance(second, Number):
            return Number(int(self.value or second.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, second)

    def notted(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        return self.value != 0
    
    def __repr__(self):
        return str(self.value)


class Function(Value):
    def __init__(self, name, body_node, arg_names):
        super().__init__()
        self.name = name or "<anonymous>"
        self.body_node = body_node
        self.arg_names = arg_names

    def execute(self, args):
        response = RTResult()
        interpreter = Interpreter()
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        if len(args) > len(self.arg_names):
            return response.failure(RTError(self.pos_start, self.pos_end, f"{len(args) - len(self.arg_names)} too many args passed into '{self.name}'", self.context))
        
        if len(args) < len(self.arg_names):
            return response.failure(RTError(self.pos_start, self.pos_end, f"{len(self.arg_names) - len(args)} too few args passed into '{self.name}'", self.context))

        for i in range(len(args)):
            arg_name = self.arg_names[i]
            arg_value = args[i]
            arg_value.set_context(new_context)
            new_context.symbol_table.set(arg_name, arg_value)

        value = response.register(interpreter.visit(self.body_node, new_context))
        if response.error: return response
        return response.success(value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"



# INTERPRETER CLASS
class Interpreter:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        #This line will create a method that makes a string with a different name depending on the type of node "visit_BinaryOpNode"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')


 #Visit methods for each node type
    def visit_NumberNode(self, node, context):
        return RTResult().success(Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_VarAccessNode(self, node, context):
        response = RTResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)

        if not value:
            return response.failure(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))
        value = value.copy().set_pos(node.pos_start, node.pos_end)
        return response.success(value)

    def visit_VarAssignNode(self, node, context):
        response = RTResult()
        var_name = node.var_name_tok.value
        value = response.register(self.visit(node.value_node, context))
        if response.error: return response
        context.symbol_table.set(var_name, value)
        return response.success(value)

    def visit_BinOpNode(self, node, context):
        response = RTResult()
        left = response.register(self.visit(node.left_node, context))
        if response.error: return response
        right = response.register(self.visit(node.right_node, context))
        if response.error: return response

        if node.op_tok.type == TT_PLUS:
            result, error = left.added_to(right)

        elif node.op_tok.type == TT_MINUS:
            result, error = left.subtracted_by(right)

        elif node.op_tok.type == TT_MUL:
            result, error = left.multiplied_by(right)

        elif node.op_tok.type == TT_DIV:
            result, error = left.divided_by(right)

        elif node.op_tok.type == TT_EXPONENT:
            result, error = left.power_of(right)

        elif node.op_tok.type == TT_EQ:
            result, error = left.get_comparison_equals(right)

        elif node.op_tok.type == TT_NE:
            result, error = left.get_comparison_notEquals(right)

        elif node.op_tok.type == TT_LT:
            result, error = left.get_comparison_lessThan(right)

        elif node.op_tok.type == TT_GT:
            result, error = left.get_comparison_greaterThan(right)

        elif node.op_tok.type == TT_LTE:
            result, error = left.get_comparison_lessThanEquals(right)

        elif node.op_tok.type == TT_GTE:
            result, error = left.get_comparison_greaterThanEquals(right)

        elif node.op_tok.matches(TT_KEYWORD, 'AND'):
            result, error = left.and_comparedTo(right)

        elif node.op_tok.matches(TT_KEYWORD, 'OR'):
            result, error = left.or_comparedTo(right)

        if error:
            return response.failure(error)

        else:
            return response.success(result.set_pos(node.pos_start, node.pos_end))


    def visit_UnaryOpNode(self, node, context):
        response = RTResult()
        number = response.register(self.visit(node.node, context))
        if response.error: return response
        error = None

        if node.op_tok.type == TT_MINUS: number, error = number.multiplied_by(Number(-1))

        elif node.op_tok.matches(TT_KEYWORD, 'NOT'): number, error = number.notted()

        if error: return response.failure(error)

        else: return response.success(number.set_pos(node.pos_start, node.pos_end))


    def visit_IfNode(self, node, context):
        response = RTResult()
        for condition, expr in node.cases:
            condition_value = response.register(self.visit(condition, context))
            if response.error: return response

            if condition_value.is_true():
                expr_value = response.register(self.visit(expr, context))
                if response.error: return response
                return response.success(expr_value)

        if node.else_case:
            else_value = response.register(self.visit(node.else_case, context))
            if response.error: return response
            return response.success(else_value)
        return response.success(None)


    def visit_ForNode(self, node, context):
        response = RTResult()
        start_value = response.register(self.visit(node.start_value_node, context))
        if response.error: return response
        end_value = response.register(self.visit(node.end_value_node, context))
        if response.error: return response

        if node.step_value_node:
            step_value = response.register(self.visit(node.step_value_node, context))
            if response.error: return response
        else: step_value = Number(1)

        i = start_value.value

        if step_value.value >= 0: condition = lambda: i < end_value.value
        else: condition = lambda: i > end_value.value
        
        while condition():
            context.symbol_table.set(node.var_name_tok.value, Number(i))
            i += step_value.value
            response.register(self.visit(node.body_node, context))
            if response.error: return response

        return response.success(None)


    def visit_WhileNode(self, node, context):
        response = RTResult()
        while True:
            condition = response.register(self.visit(node.condition_node, context))
            if response.error: return response
            if not condition.is_true(): break
            response.register(self.visit(node.body_node, context))
            if response.error: return response
        return response.success(None)


    def visit_FuncDefNode(self, node, context):
        response = RTResult()
        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        func_value = Function(func_name, body_node, arg_names).set_context(context).set_pos(node.pos_start, node.pos_end)
        
        if node.var_name_tok:
            context.symbol_table.set(func_name, func_value)
        return response.success(func_value)


    def visit_CallNode(self, node, context):
        response = RTResult()
        args = []
        value_to_call = response.register(self.visit(node.node_to_call, context))
        if response.error: return response
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(response.register(self.visit(arg_node, context)))
            if response.error: return response

        return_value = response.register(value_to_call.execute(args))
        if response.error: return response
        return response.success(return_value)



##############################################################################################################
##                                     RUN CODE
##############################################################################################################

#Global Symbol Table
global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number(0))
global_symbol_table.set("FALSE", Number(0))
global_symbol_table.set("TRUE", Number(1))


def run(fn, text):
    # Token generator
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error
    
    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    # Run interpreter
    interpreter = Interpreter()
    context = Context('<runningProgram>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error

# Possible operands for later
# reserved = {
#     'display': 'DISPLAY',
#     'for': 'FOR',
#     'if': 'IF',
#     'else': 'ELSE',
#     'while': 'WHILE',
#     'greaterThan': 'GREATERTHAN',
#     'lessThan': 'LESSTHAN',
#     'equals': 'EQUALS',
#     'end': 'END',
#     'and': 'AND',
#     'exact': 'EXACT',
#     'between': 'BETWEEN',
#     'endBlock': 'ENDBLOCK',
#     'att': 'ATTRIBUTE'
# }