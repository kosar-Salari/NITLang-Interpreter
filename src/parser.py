from token_types import TokenType
from ast_nodes import (
    Number, BinaryOp, Identifier, FunctionDef,
    FunctionCall, IfExpr, Comparison, LetStatement,
    LetExpression, Block, RefExpr, DerefExpr, RefAssign,
    BoolLiteral, StringLiteral,
    FieldDef, ClassDef, NewExpr, MemberAccess, MethodCall, Assign
)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None

    def error(self, msg="Invalid syntax"):
        raise Exception(f'{msg} at position {self.pos}, token: {self.current_token}')

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.advance()
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type}")

    # -------------------------------
    # primary (basic atoms)
    # -------------------------------
    def primary(self):
        token = self.current_token

        # ref a
        if token.type == TokenType.REF:
            self.eat(TokenType.REF)
            name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)
            return RefExpr(Identifier(name))

        # #a
        if token.type == TokenType.DEREF:
            self.eat(TokenType.DEREF)
            name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)
            return DerefExpr(Identifier(name))

        # new Class(...)
        if token.type == TokenType.NEW:
            self.eat(TokenType.NEW)
            class_name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)
            self.eat(TokenType.LPAREN)
            args = self.arguments()
            self.eat(TokenType.RPAREN)
            return NewExpr(class_name, args)

        # number
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(token.value)

        # bool
        if token.type == TokenType.BOOL:
            val = (token.value == 'true')
            self.eat(TokenType.BOOL)
            return BoolLiteral(val)

        # string
        if token.type == TokenType.STRING:
            val = token.value
            self.eat(TokenType.STRING)
            return StringLiteral(val)

        # identifier / function call (global)
        if token.type == TokenType.IDENTIFIER:
            name = token.value
            self.eat(TokenType.IDENTIFIER)

            if self.current_token.type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                args = self.arguments()
                self.eat(TokenType.RPAREN)
                return FunctionCall(name, args)

            return Identifier(name)

        # (expr)
        if token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node

        self.error("Expected primary expression")

    # -------------------------------
    # postfix (member access / method calls)
    # -------------------------------
    def factor(self):
        node = self.primary()

        while self.current_token.type == TokenType.DOT:
            self.eat(TokenType.DOT)
            member_name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)

            if self.current_token.type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                args = self.arguments()
                self.eat(TokenType.RPAREN)
                node = MethodCall(node, member_name, args)
            else:
                node = MemberAccess(node, member_name)

        return node

    # -------------------------------
    # term / arith_expr / comparison
    # -------------------------------
    def term(self):
        node = self.factor()

        while self.current_token.type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.current_token.type
            self.eat(op)
            node = BinaryOp(node, op, self.factor())

        return node

    def arith_expr(self):
        node = self.term()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token.type
            self.eat(op)
            node = BinaryOp(node, op, self.term())

        return node

    def comparison(self):
        node = self.arith_expr()

        if self.current_token.type == TokenType.EQUALS:
            op = self.current_token.type
            self.eat(TokenType.EQUALS)
            node = Comparison(node, op, self.arith_expr())

        return node

    # -------------------------------
    # expressions
    # -------------------------------
    def expr(self):

        # if-expression
        if self.current_token.type == TokenType.IF:
            self.eat(TokenType.IF)
            cond = self.expr()
            self.eat(TokenType.THEN)
            tbranch = self.expr()
            self.eat(TokenType.ELSE)
            fbranch = self.expr()
            return IfExpr(cond, tbranch, fbranch)

        # let-expression
        if self.current_token.type == TokenType.LET:
            self.eat(TokenType.LET)
            var_name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)

            type_ann = None
            if self.current_token.type == TokenType.COLON:
                self.eat(TokenType.COLON)
                type_ann = self.current_token.value
                self.eat(TokenType.IDENTIFIER)

            self.eat(TokenType.ASSIGN)
            value_expr = self.expr()

            if self.current_token.type != TokenType.IN:
                self.error("let-expression must contain 'in'")

            self.eat(TokenType.IN)

            if self.current_token.type == TokenType.LBRACE:
                body = self.block_expression()
            else:
                body = self.expr()

            return LetExpression(var_name, type_ann, value_expr, body)

        # block as expr
        if self.current_token.type == TokenType.LBRACE:
            return self.block_expression()

        return self.comparison()

    # -------------------------------
    # block
    # -------------------------------
    def block_expression(self):
        self.eat(TokenType.LBRACE)
        statements = []
        while self.current_token.type != TokenType.RBRACE:
            statements.append(self.statement())
        self.eat(TokenType.RBRACE)
        return Block(statements)

    # -------------------------------
    # class definition
    # -------------------------------
    def parse_class(self):
        self.eat(TokenType.CLASS)
        class_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.LBRACE)

        fields = []
        methods = []

        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.LET:
                # field declaration: let x:int
                self.eat(TokenType.LET)
                fname = self.current_token.value
                self.eat(TokenType.IDENTIFIER)

                type_ann = None
                if self.current_token.type == TokenType.COLON:
                    self.eat(TokenType.COLON)
                    type_ann = self.current_token.value
                    self.eat(TokenType.IDENTIFIER)

                fields.append(FieldDef(fname, type_ann))

            elif self.current_token.type == TokenType.FUNC:
                # method: func m(params) = { ... }
                self.eat(TokenType.FUNC)
                mname = self.current_token.value
                self.eat(TokenType.IDENTIFIER)
                self.eat(TokenType.LPAREN)
                params = self.parameters()
                self.eat(TokenType.RPAREN)
                self.eat(TokenType.ASSIGN)

                if self.current_token.type == TokenType.LBRACE:
                    self.eat(TokenType.LBRACE)
                    stmts = []
                    while self.current_token.type != TokenType.RBRACE:
                        stmts.append(self.statement())
                    self.eat(TokenType.RBRACE)
                    body = Block(stmts)
                else:
                    body = self.expr()

                methods.append(FunctionDef(mname, params, body))

            else:
                self.error("Expected field or method in class body")

        self.eat(TokenType.RBRACE)
        return ClassDef(class_name, fields, methods)

    # -------------------------------
    # statements
    # -------------------------------
    def statement(self):

        # class
        if self.current_token.type == TokenType.CLASS:
            return self.parse_class()

        # let
        if self.current_token.type == TokenType.LET:
            self.eat(TokenType.LET)
            var_name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)

            type_ann = None
            if self.current_token.type == TokenType.COLON:
                self.eat(TokenType.COLON)
                type_ann = self.current_token.value
                self.eat(TokenType.IDENTIFIER)

            self.eat(TokenType.ASSIGN)
            val = self.expr()

            if self.current_token.type == TokenType.IN:
                self.eat(TokenType.IN)
                return LetExpression(var_name, type_ann, val, self.expr())

            return LetStatement(var_name, type_ann, val)

        # function (global)
        if self.current_token.type == TokenType.FUNC:
            self.eat(TokenType.FUNC)
            name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)
            self.eat(TokenType.LPAREN)
            params = self.parameters()
            self.eat(TokenType.RPAREN)
            self.eat(TokenType.ASSIGN)

            if self.current_token.type == TokenType.LBRACE:
                self.eat(TokenType.LBRACE)
                stmts = []
                while self.current_token.type != TokenType.RBRACE:
                    stmts.append(self.statement())
                self.eat(TokenType.RBRACE)
                body = Block(stmts)
            else:
                body = self.expr()

            return FunctionDef(name, params, body)

        # otherwise: expr / assignment / ref-assign
        left = self.expr()

        # ref assignment: a := expr
        if self.current_token.type == TokenType.COLON_ASSIGN:
            self.eat(TokenType.COLON_ASSIGN)
            value = self.expr()
            return RefAssign(left, value)

        # normal assignment: x = expr یا obj.field = expr
        if self.current_token.type == TokenType.ASSIGN:
            self.eat(TokenType.ASSIGN)
            value = self.expr()
            if not isinstance(left, (Identifier, MemberAccess)):
                self.error("Invalid assignment target")
            return Assign(left, value)

        return left

    # -------------------------------
    # misc
    # -------------------------------
    def arguments(self):
        args = []
        if self.current_token.type == TokenType.RPAREN:
            return args

        args.append(self.expr())
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            args.append(self.expr())
        return args

    def parameters(self):
        params = []
        if self.current_token.type == TokenType.RPAREN:
            return params

        params.append(self.current_token.value)
        self.eat(TokenType.IDENTIFIER)

        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            params.append(self.current_token.value)
            self.eat(TokenType.IDENTIFIER)

        return params

    def parse(self):
        node = self.statement()
        if self.current_token.type != TokenType.EOF:
            self.error("Expected end of input")
        return node
