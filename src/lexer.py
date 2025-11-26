from token_types import Token, TokenType, KEYWORDS


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if text else None

    def error(self):
        raise Exception(f'Invalid character "{self.current_char}" at position {self.pos}')

    def advance(self):
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos >= len(self.text):
            return None
        return self.text[peek_pos]

    def skip_whitespace(self):
        while self.current_char and self.current_char in ' \t\n\r':
            self.advance()

    def number(self):
        result = ''
        start_pos = self.pos
        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return Token(TokenType.NUMBER, int(result), start_pos)

    def string_literal(self):
        start_pos = self.pos
        self.advance()  # skip opening "
        result = ''
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        if self.current_char != '"':
            self.error()
        self.advance()  # skip closing "
        return Token(TokenType.STRING, result, start_pos)

    def identifier(self):
        result = ''
        start_pos = self.pos
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        token_type = KEYWORDS.get(result, TokenType.IDENTIFIER)
        return Token(token_type, result, start_pos)

    def get_next_token(self):
        while self.current_char:

            # whitespace
            if self.current_char in ' \t\n\r':
                self.skip_whitespace()
                continue

            # string literal
            if self.current_char == '"':
                return self.string_literal()

            # number
            if self.current_char and self.current_char.isdigit():
                return self.number()

            # identifier / keyword
            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()

            # :=
            if self.current_char == ':' and self.peek() == '=':
                pos = self.pos
                self.advance()
                self.advance()
                return Token(TokenType.COLON_ASSIGN, ':=', pos)

            # :
            if self.current_char == ':':
                pos = self.pos
                self.advance()
                return Token(TokenType.COLON, ':', pos)

            # .
            if self.current_char == '.':
                pos = self.pos
                self.advance()
                return Token(TokenType.DOT, '.', pos)

            # operators
            if self.current_char == '+':
                pos = self.pos
                self.advance()
                return Token(TokenType.PLUS, '+', pos)

            if self.current_char == '-':
                pos = self.pos
                self.advance()
                return Token(TokenType.MINUS, '-', pos)

            if self.current_char == '*':
                pos = self.pos
                self.advance()
                return Token(TokenType.MULTIPLY, '*', pos)

            if self.current_char == '/':
                pos = self.pos
                self.advance()
                return Token(TokenType.DIVIDE, '/', pos)

            # = or ==
            if self.current_char == '=':
                pos = self.pos
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.EQUALS, '==', pos)
                return Token(TokenType.ASSIGN, '=', pos)

            # braces
            if self.current_char == '{':
                pos = self.pos
                self.advance()
                return Token(TokenType.LBRACE, '{', pos)

            if self.current_char == '}':
                pos = self.pos
                self.advance()
                return Token(TokenType.RBRACE, '}', pos)

            # parentheses
            if self.current_char == '(':
                pos = self.pos
                self.advance()
                return Token(TokenType.LPAREN, '(', pos)

            if self.current_char == ')':
                pos = self.pos
                self.advance()
                return Token(TokenType.RPAREN, ')', pos)

            # comma
            if self.current_char == ',':
                pos = self.pos
                self.advance()
                return Token(TokenType.COMMA, ',', pos)

            # DEREF operator (#)
            if self.current_char == '#':
                pos = self.pos
                self.advance()
                return Token(TokenType.DEREF, '#', pos)

            self.error()

        return Token(TokenType.EOF, None, self.pos)

    def tokenize(self):
        tokens = []
        token = self.get_next_token()
        while token.type != TokenType.EOF:
            tokens.append(token)
            token = self.get_next_token()
        tokens.append(token)
        return tokens
