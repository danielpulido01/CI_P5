from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Any


class TokenType(Enum):
    INT        = auto()
    REAL       = auto()
    BOOL       = auto()
    IDENT      = auto()
    LAMBDA     = auto()
    FUN        = auto()
    LET        = auto()
    IN         = auto()
    IF         = auto()
    THEN       = auto()
    ELSE       = auto()
    DIV        = auto()
    PLUS       = auto()
    MINUS      = auto()
    STAR       = auto()
    SLASH      = auto()
    PERCENT    = auto()
    AMP        = auto()
    PIPE       = auto()
    BANG       = auto()
    CARET      = auto()
    EQ         = auto()
    LT         = auto()
    GT         = auto()
    LEQ        = auto()
    GEQ        = auto()
    NEQ        = auto()
    LPAREN     = auto()
    RPAREN     = auto()
    COMMA      = auto()
    SEMICOLON  = auto()
    TILDE      = auto()
    EOF        = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"


_KEYWORDS = {
    'lambda': TokenType.LAMBDA,
    'fun':    TokenType.FUN,
    'let':    TokenType.LET,
    'in':     TokenType.IN,
    'if':     TokenType.IF,
    'then':   TokenType.THEN,
    'else':   TokenType.ELSE,
    'div':    TokenType.DIV,
    'true':   TokenType.BOOL,
    'false':  TokenType.BOOL,
}

_SINGLE = {
    '+': TokenType.PLUS,
    '-': TokenType.MINUS,
    '*': TokenType.STAR,
    '/': TokenType.SLASH,
    '%': TokenType.PERCENT,
    '&': TokenType.AMP,
    '|': TokenType.PIPE,
    '!': TokenType.BANG,
    '^': TokenType.CARET,
    '=': TokenType.EQ,
    '<': TokenType.LT,
    '>': TokenType.GT,
    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    ',': TokenType.COMMA,
    ';': TokenType.SEMICOLON,
    '~': TokenType.TILDE,
}


class LexError(Exception):
    pass


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    n = len(source)

    while i < n:
        c = source[i]

        # Whitespace
        if c in ' \t\r':
            i += 1
            continue
        if c == '\n':
            line += 1
            i += 1
            continue

        # Comments: # to end of line
        if c == '#':
            while i < n and source[i] != '\n':
                i += 1
            continue

        # Numbers: int or real
        if c.isdigit():
            j = i
            while j < n and source[j].isdigit():
                j += 1
            if j < n and source[j] == '.' and j + 1 < n and source[j + 1].isdigit():
                j += 1
                while j < n and source[j].isdigit():
                    j += 1
                tokens.append(Token(TokenType.REAL, float(source[i:j]), line))
            else:
                tokens.append(Token(TokenType.INT, int(source[i:j]), line))
            i = j
            continue

        # Identifiers and keywords
        if c.isalpha() or c == '_':
            j = i
            while j < n and (source[j].isalnum() or source[j] == '_'):
                j += 1
            word = source[i:j]
            if word in _KEYWORDS:
                tt = _KEYWORDS[word]
                val = True if word == 'true' else (False if word == 'false' else word)
                tokens.append(Token(tt, val, line))
            else:
                tokens.append(Token(TokenType.IDENT, word, line))
            i = j
            continue

        # Two-character operators
        two = source[i:i + 2]
        if two == '<=':
            tokens.append(Token(TokenType.LEQ, '<=', line)); i += 2; continue
        if two == '>=':
            tokens.append(Token(TokenType.GEQ, '>=', line)); i += 2; continue
        if two == '!=':
            tokens.append(Token(TokenType.NEQ, '!=', line)); i += 2; continue

        # Single-character operators / punctuation
        if c in _SINGLE:
            tokens.append(Token(_SINGLE[c], c, line))
            i += 1
            continue

        raise LexError(f"Unexpected character {c!r} at line {line}")

    tokens.append(Token(TokenType.EOF, None, line))
    return tokens
