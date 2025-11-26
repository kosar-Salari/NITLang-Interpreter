from enum import Enum


class TokenType(Enum):
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"

    FUNC = "FUNC"
    IF = "IF"
    THEN = "THEN"
    ELSE = "ELSE"
    LET = "LET"
    IN = "IN"

    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    EQUALS = "EQUALS"
    ASSIGN = "ASSIGN"

    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    HASH = "HASH"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"

    COLON_ASSIGN = "COLON_ASSIGN"  # :=
    REF = "REF"                    # ref
    DEREF = "DEREF"                # #

    COLON = "COLON"                # :
    STRING = "STRING"              # "foo"
    BOOL = "BOOL"                  # true / false

    CLASS = "CLASS"                # class
    NEW = "NEW"                    # new
    DOT = "DOT"                    # .

    EOF = "EOF"


class Token:
    def __init__(self, type, value, position):
        self.type = type
        self.value = value
        self.position = position

    def __repr__(self):
        return f"Token({self.type}, {self.value}, pos={self.position})"


KEYWORDS = {
    'func': TokenType.FUNC,
    'if': TokenType.IF,
    'then': TokenType.THEN,
    'else': TokenType.ELSE,
    'let': TokenType.LET,
    'in': TokenType.IN,
    'ref': TokenType.REF,

    'true': TokenType.BOOL,
    'false': TokenType.BOOL,

    'class': TokenType.CLASS,
    'new': TokenType.NEW,
}
