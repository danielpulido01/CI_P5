from typing import List, Optional, Tuple, Union
from .lexer import Token, TokenType, tokenize, LexError
from .ast_nodes import (
    Node, IntLit, RealLit, BoolLit, Ident, BinOp, UnaryOp,
    Lambda, FuncCall, IfExpr, LetExpr, Definition, Program,
)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── token navigation ──────────────────────────────────────────────────

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, tt: TokenType) -> Token:
        t = self.advance()
        if t.type != tt:
            raise ParseError(
                f"Expected {tt.name}, got {t.type.name} ({t.value!r}) at line {t.line}"
            )
        return t

    def match(self, *types: TokenType) -> Optional[Token]:
        if self.peek().type in types:
            return self.advance()
        return None

    def check(self, *types: TokenType) -> bool:
        return self.peek().type in types

    # ── top-level ─────────────────────────────────────────────────────────

    def parse_program(self) -> Program:
        defs: List[Definition] = []
        while not self.check(TokenType.EOF):
            d = self.parse_definition()
            defs.append(d)
            if not self.match(TokenType.SEMICOLON):
                break
            if self.check(TokenType.EOF):
                break
        self.expect(TokenType.EOF)
        return Program(defs)

    def parse_definition(self) -> Definition:
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.EQ)
        expr = self.parse_expr()
        return Definition(name_tok.value, expr)

    # ── expressions ───────────────────────────────────────────────────────

    def parse_expr(self) -> Node:
        if self.check(TokenType.LET):
            return self.parse_let()
        if self.check(TokenType.IF):
            return self.parse_if()
        if self.check(TokenType.LAMBDA, TokenType.FUN):
            return self.parse_lambda()
        return self.parse_bool_expr()

    # -- let ---------------------------------------------------------------

    def parse_let(self) -> LetExpr:
        self.expect(TokenType.LET)
        defs: List[Tuple[str, Node]] = []

        while True:
            name_tok = self.expect(TokenType.IDENT)
            self.expect(TokenType.EQ)
            expr = self.parse_expr()
            defs.append((name_tok.value, expr))

            # semicolon is a separator between let bindings
            if self.match(TokenType.SEMICOLON):
                if self.check(TokenType.IN):
                    break           # trailing semicolon before 'in'
                continue            # another binding follows
            break                   # no semicolon → last binding

        self.expect(TokenType.IN)
        body = self.parse_expr()
        return LetExpr(defs, body)

    # -- if ----------------------------------------------------------------

    def parse_if(self) -> IfExpr:
        self.expect(TokenType.IF)
        cond = self.parse_expr()
        self.expect(TokenType.THEN)
        then_e = self.parse_expr()
        self.expect(TokenType.ELSE)
        else_e = self.parse_expr()
        return IfExpr(cond, then_e, else_e)

    # -- lambda / fun ------------------------------------------------------

    def parse_lambda(self) -> Lambda:
        self.advance()              # consume 'lambda' or 'fun'
        self.expect(TokenType.LPAREN)
        params: List[str] = []
        if not self.check(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENT).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)
        self.match(TokenType.TILDE)  # optional ~ separator
        body = self.parse_expr()
        return Lambda(params, body)

    # -- boolean layer ---------------------------------------------------- &, |, ^

    def parse_bool_expr(self) -> Node:
        left = self.parse_cmp_expr()
        while self.check(TokenType.AMP, TokenType.PIPE, TokenType.CARET):
            op = self.advance().value
            right = self.parse_cmp_expr()
            left = BinOp(op, left, right)
        return left

    # -- comparison layer ------------------------------------------------- =, <, >, <=, >=, !=

    def parse_cmp_expr(self) -> Node:
        left = self.parse_add_expr()
        while self.check(
            TokenType.EQ, TokenType.LT, TokenType.GT,
            TokenType.LEQ, TokenType.GEQ, TokenType.NEQ,
        ):
            op = self.advance().value
            right = self.parse_add_expr()
            left = BinOp(op, left, right)
        return left

    # -- additive layer --------------------------------------------------- +, -

    def parse_add_expr(self) -> Node:
        left = self.parse_mul_expr()
        while self.check(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_mul_expr()
            left = BinOp(op, left, right)
        return left

    # -- multiplicative layer --------------------------------------------- *, /, div, %

    def parse_mul_expr(self) -> Node:
        left = self.parse_unary()
        while self.check(
            TokenType.STAR, TokenType.SLASH, TokenType.DIV, TokenType.PERCENT
        ):
            op = self.advance().value
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left

    # -- unary ------------------------------------------------------------ !, -

    def parse_unary(self) -> Node:
        if self.match(TokenType.BANG):
            return UnaryOp('!', self.parse_unary())
        if self.match(TokenType.MINUS):
            # Negative number literal optimisation
            t = self.peek()
            if t.type == TokenType.INT:
                self.advance()
                return IntLit(-t.value)
            if t.type == TokenType.REAL:
                self.advance()
                return RealLit(-t.value)
            return UnaryOp('-', self.parse_unary())
        return self.parse_postfix()

    # -- postfix call ----------------------------------------------------- f(args)

    def parse_postfix(self) -> Node:
        node = self.parse_primary()
        while self.check(TokenType.LPAREN):
            self.advance()
            args: List[Node] = []
            if not self.check(TokenType.RPAREN):
                args.append(self.parse_expr())
                while self.match(TokenType.COMMA):
                    args.append(self.parse_expr())
            self.expect(TokenType.RPAREN)
            node = FuncCall(node, args)
        return node

    # -- primary ---------------------------------------------------------- literals, ident, (expr)

    def parse_primary(self) -> Node:
        t = self.peek()
        if t.type == TokenType.INT:
            self.advance()
            return IntLit(t.value)
        if t.type == TokenType.REAL:
            self.advance()
            return RealLit(t.value)
        if t.type == TokenType.BOOL:
            self.advance()
            return BoolLit(t.value)
        if t.type == TokenType.IDENT:
            self.advance()
            return Ident(t.value)
        if t.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        raise ParseError(
            f"Unexpected token {t.type.name} ({t.value!r}) at line {t.line}"
        )


# ── public helpers ────────────────────────────────────────────────────────────

def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens).parse_program()


def parse_expr_only(source: str) -> Node:
    tokens = tokenize(source)
    p = Parser(tokens)
    expr = p.parse_expr()
    p.expect(TokenType.EOF)
    return expr


def parse_shell_input(source: str) -> Union[Definition, Node]:
    """Parse a single shell line as either a definition or an expression."""
    tokens = tokenize(source)
    # Heuristic: IDENT '=' and the third token is NOT a comparison operator
    # → treat as definition.  Otherwise parse as expression.
    if (
        len(tokens) >= 3
        and tokens[0].type == TokenType.IDENT
        and tokens[1].type == TokenType.EQ
    ):
        p = Parser(tokens)
        d = p.parse_definition()
        p.expect(TokenType.EOF)
        return d
    p = Parser(tokens)
    expr = p.parse_expr()
    p.expect(TokenType.EOF)
    return expr
