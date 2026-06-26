"""Parser a discesa ricorsiva per InclusiveScript.

Trasforma la lista di Token in un AST (lista di istruzioni).

Grammatica (in ordine di precedenza crescente):

    program     -> declaration* EOF
    declaration -> funDecl | fluidDecl | statement
    funDecl     -> "fun" IDENTIFIER "(" params? ")" block
    fluidDecl   -> "fluid" ( "binary" | "nonbinary" | "group" )? IDENTIFIER ( "feels" expression )? ";"?
                   (tipo omesso = inferito dal valore; ';' opzionale)
    statement   -> exprStmt | ifStmt | whileStmt | cycleStmt | beStmt | returnStmt | block
    beStmt      -> "be" primary ( expression ( "," expression )* )? ";"?
                   (invocazione senza parentesi: be print "")
    exprStmt    -> expression ( ";" | block ( "else" statement )? )?
                   (expression seguita da un blocco = 'if' implicito, condizione = expression)
    block       -> "{" declaration* "}"        ("{"/"}" anche scritti ❤️ / 💔)
    expression  -> assignment
    assignment  -> ( IDENTIFIER | index ) "feels" assignment
                 | call ( "inclusive" | "exclusive" ) assignment
                 | logic_or
    logic_or    -> logic_and ( "or" logic_and )*
    logic_and   -> equality ( "and" equality )*
    equality    -> comparison ( ( "likes" | "unlikes" ) comparison )*
    comparison  -> term ( ( "over" | "overlikes" | "under" | "underlikes" ) term )*
    term        -> factor ( ( "+" | "-" ) factor )*
    factor      -> unary ( ( "*" | "/" ) unary )*
    unary       -> ( "not" | "-" ) unary | call
    call        -> primary ( "(" arguments? ")" | "[" expression "]" )*
    primary     -> NUMBER | STRING | "king" | "queen" | "bi" | "nil"
                 | "(" expression ")" | IDENTIFIER | list
    list        -> "[" ( expression ( "," expression )* )? "]"
"""

from __future__ import annotations

from typing import List, Optional

from . import ast_nodes as ast
from .environment import BI
from .errors import ParseError
from .tokens import Token, TokenType


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> List[ast.Stmt]:
        statements: List[ast.Stmt] = []
        while not self._is_at_end():
            statements.append(self._declaration())
        return statements

    # --- helper ------------------------------------------------------------------

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, type_: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type_

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, type_: TokenType, message: str) -> Token:
        if self._check(type_):
            return self._advance()
        raise ParseError(message, self._peek().line)

    # --- dichiarazioni -----------------------------------------------------------

    def _declaration(self) -> ast.Stmt:
        if self._match(TokenType.FUN):
            return self._function("funzione")
        if self._match(TokenType.FLUID):
            return self._fluid_declaration()
        return self._statement()

    def _function(self, kind: str) -> ast.Function:
        name = self._consume(TokenType.IDENTIFIER, f"Atteso nome della {kind}.")
        self._consume(TokenType.LEFT_PAREN, f"Attesa '(' dopo il nome della {kind}.")
        params: List[Token] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(params) >= 255:
                    raise ParseError("Una funzione non puo' avere piu' di 255 parametri.", self._peek().line)
                params.append(self._consume(TokenType.IDENTIFIER, "Atteso nome del parametro."))
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RIGHT_PAREN, "Attesa ')' dopo i parametri.")
        self._consume(TokenType.LEFT_BRACE, f"Attesa '{{' prima del corpo della {kind}.")
        body = self._block()
        return ast.Function(name, params, body)

    def _fluid_declaration(self) -> ast.Stmt:
        # Il tipo è opzionale: binary / nonbinary / group. Se assente, viene
        # inferito dal valore iniziale (a runtime).
        declared_type: Optional[str] = None
        if self._match(TokenType.BINARY):
            declared_type = "binary"
        elif self._match(TokenType.NONBINARY):
            declared_type = "nonbinary"
        elif self._match(TokenType.GROUP):
            declared_type = "group"
        name = self._consume(
            TokenType.IDENTIFIER,
            "Atteso il nome della variabile (eventualmente preceduto dal tipo).",
        )
        initializer: Optional[ast.Expr] = None
        if self._match(TokenType.FEELS):
            initializer = self._expression()
        self._match(TokenType.SEMICOLON)  # ';' opzionale
        return ast.FluidStmt(name, declared_type, initializer)

    # --- istruzioni --------------------------------------------------------------

    def _statement(self) -> ast.Stmt:
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.CYCLE):
            return self._cycle_statement()
        if self._match(TokenType.BE):
            return self._be_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.LEFT_BRACE):
            return ast.Block(self._block())
        return self._expression_statement()

    def _if_statement(self) -> ast.Stmt:
        self._consume(TokenType.LEFT_PAREN, "Attesa '(' dopo 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Attesa ')' dopo la condizione dell'if.")
        then_branch = self._statement()
        else_branch: Optional[ast.Stmt] = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()
        return ast.If(condition, then_branch, else_branch)

    def _while_statement(self) -> ast.Stmt:
        self._consume(TokenType.LEFT_PAREN, "Attesa '(' dopo 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Attesa ')' dopo la condizione del while.")
        body = self._statement()
        return ast.While(condition, body)

    def _cycle_statement(self) -> ast.Stmt:
        # cycle ( item , index in <espressione> ) { ... }
        self._consume(TokenType.LEFT_PAREN, "Attesa '(' dopo 'cycle'.")
        item = self._consume(TokenType.IDENTIFIER, "Atteso il nome dell'elemento (item).")
        self._consume(TokenType.COMMA, "Atteso ',' tra item e index.")
        index = self._consume(TokenType.IDENTIFIER, "Atteso il nome dell'indice (index).")
        self._consume(TokenType.IN, "Atteso 'in' dopo 'item, index'.")
        iterable = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Attesa ')' dopo l'espressione del cycle.")
        self._consume(TokenType.LEFT_BRACE, "Atteso '❤️' (o '{') per aprire il corpo del cycle.")
        body = self._block()
        return ast.Cycle(item, index, iterable, body)

    # Token che possono iniziare un'espressione (per capire dove finiscono gli
    # argomenti di 'be' senza bisogno di parentesi).
    _EXPR_START = {
        TokenType.NUMBER,
        TokenType.STRING,
        TokenType.IDENTIFIER,
        TokenType.TRUE,
        TokenType.FALSE,
        TokenType.BI,
        TokenType.NIL,
        TokenType.LEFT_PAREN,
        TokenType.LEFT_BRACKET,
        TokenType.BANG,
        TokenType.MINUS,
    }

    def _starts_expression(self) -> bool:
        return self._peek().type in self._EXPR_START

    def _be_statement(self) -> ast.Stmt:
        # be <funzione> <primo arg>? ( "," <arg> )*
        # Es: be print ""   ->   chiama print con l'argomento "".
        be_token = self._previous()
        callee = self._primary()  # il riferimento alla funzione (un atomo)
        arguments: List[ast.Expr] = []
        if self._starts_expression():
            arguments.append(self._expression())
            while self._match(TokenType.COMMA):
                arguments.append(self._expression())
        self._match(TokenType.SEMICOLON)  # ';' opzionale
        # 'be' è zucchero: produce lo stesso nodo Call della forma con parentesi.
        return ast.ExpressionStmt(ast.Call(callee, be_token, arguments))

    def _return_statement(self) -> ast.Stmt:
        keyword = self._previous()
        value: Optional[ast.Expr] = None
        # C'è un valore a meno che non segua subito ';', la fine del blocco o EOF.
        if not (
            self._check(TokenType.SEMICOLON)
            or self._check(TokenType.RIGHT_BRACE)
            or self._is_at_end()
        ):
            value = self._expression()
        self._match(TokenType.SEMICOLON)  # ';' opzionale
        return ast.Return(keyword, value)

    def _block(self) -> List[ast.Stmt]:
        statements: List[ast.Stmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._declaration())
        self._consume(TokenType.RIGHT_BRACE, "Attesa '}' dopo il blocco.")
        return statements

    def _expression_statement(self) -> ast.Stmt:
        expr = self._expression()
        # Un ';' chiude esplicitamente l'istruzione.
        if self._match(TokenType.SEMICOLON):
            return ast.ExpressionStmt(expr)
        # Senza ';', se segue un blocco (❤️ / {) allora è un 'if' implicito:
        #   <condizione> ❤️ ... 💔 [ else ... ]
        if self._check(TokenType.LEFT_BRACE):
            self._advance()  # consuma ❤️ / {
            then_branch = ast.Block(self._block())
            else_branch: Optional[ast.Stmt] = None
            if self._match(TokenType.ELSE):
                else_branch = self._statement()
            return ast.If(expr, then_branch, else_branch)
        # Altrimenti è una normale istruzione-espressione (';' opzionale assente).
        return ast.ExpressionStmt(expr)

    # --- espressioni -------------------------------------------------------------

    def _expression(self) -> ast.Expr:
        return self._assignment()

    def _assignment(self) -> ast.Expr:
        expr = self._or()
        if self._match(TokenType.FEELS):
            feels = self._previous()
            value = self._assignment()
            if isinstance(expr, ast.Variable):
                return ast.Assign(expr.name, value)
            if isinstance(expr, ast.IndexGet):
                return ast.IndexSet(expr.collection, expr.bracket, expr.index, value)
            raise ParseError("A sinistra di 'feels' serve una variabile o un elemento di lista.", feels.line)
        if self._match(TokenType.INCLUSIVE, TokenType.EXCLUSIVE):
            op = self._previous()
            value = self._assignment()
            return ast.ListMutate(expr, op, value)
        return expr

    def _or(self) -> ast.Expr:
        expr = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._and()
            expr = ast.Logical(expr, operator, right)
        return expr

    def _and(self) -> ast.Expr:
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = ast.Logical(expr, operator, right)
        return expr

    def _equality(self) -> ast.Expr:
        expr = self._comparison()
        # likes -> ==, unlikes -> !=
        while self._match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _comparison(self) -> ast.Expr:
        expr = self._term()
        while self._match(
            TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL
        ):
            operator = self._previous()
            right = self._term()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _term(self) -> ast.Expr:
        expr = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _factor(self) -> ast.Expr:
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous()
            right = self._unary()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _unary(self) -> ast.Expr:
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return ast.Unary(operator, right)
        return self._call()

    def _call(self) -> ast.Expr:
        expr = self._primary()
        while True:
            if self._match(TokenType.LEFT_PAREN):
                expr = self._finish_call(expr)
            elif self._match(TokenType.LEFT_BRACKET):
                bracket = self._previous()
                index = self._expression()
                self._consume(TokenType.RIGHT_BRACKET, "Attesa ']' dopo l'indice.")
                expr = ast.IndexGet(expr, bracket, index)
            else:
                break
        return expr

    def _finish_call(self, callee: ast.Expr) -> ast.Expr:
        arguments: List[ast.Expr] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    raise ParseError("Una chiamata non puo' avere piu' di 255 argomenti.", self._peek().line)
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
        paren = self._consume(TokenType.RIGHT_PAREN, "Attesa ')' dopo gli argomenti.")
        return ast.Call(callee, paren, arguments)

    def _primary(self) -> ast.Expr:
        if self._match(TokenType.FALSE):
            return ast.Literal(False)
        if self._match(TokenType.TRUE):
            return ast.Literal(True)
        if self._match(TokenType.NIL):
            return ast.Literal(None)
        if self._match(TokenType.BI):
            return ast.Literal(BI)
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return ast.Literal(self._previous().literal)
        if self._match(TokenType.IDENTIFIER):
            return ast.Variable(self._previous())
        if self._match(TokenType.LEFT_BRACKET):
            elements: List[ast.Expr] = []
            if not self._check(TokenType.RIGHT_BRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACKET, "Attesa ']' per chiudere la lista.")
            return ast.ListLiteral(elements)
        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Attesa ')' dopo l'espressione.")
            return ast.Grouping(expr)
        raise ParseError("Attesa un'espressione.", self._peek().line)
