"""Lexer (tokenizzatore) di InclusiveScript.

Trasforma il testo sorgente in una lista di Token.
"""

from __future__ import annotations

from typing import List

from .errors import LexerError
from .tokens import KEYWORDS, Token, TokenType

# I cuori fanno da parentesi graffe: ❤️ = '{', 💔 = '}'.
# Il cuore rosso puo' arrivare con o senza "variation selector" (U+FE0F),
# quindi gestiamo entrambe le forme; la piu' lunga va controllata per prima.
HEARTS = [
    ("❤️", TokenType.LEFT_BRACE),   # ❤️
    ("❤", TokenType.LEFT_BRACE),          # ❤
    ("\U0001f494", TokenType.RIGHT_BRACE),     # 💔
]


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> List[Token]:
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    # --- helper di basso livello -------------------------------------------------

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        return ch

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _add_token(self, type_: TokenType, literal=None) -> None:
        text = self.source[self.start : self.current]
        self.tokens.append(Token(type_, text, literal, self.line))

    # --- scansione ---------------------------------------------------------------

    def _scan_token(self) -> None:
        # I cuori sono parentesi graffe (possibili sequenze multi-carattere)
        for heart, ttype in HEARTS:
            if self.source.startswith(heart, self.current):
                self.current += len(heart)
                self._add_token(ttype)
                return

        c = self._advance()
        if c == "(":
            self._add_token(TokenType.LEFT_PAREN)
        elif c == ")":
            self._add_token(TokenType.RIGHT_PAREN)
        elif c == "{":
            self._add_token(TokenType.LEFT_BRACE)
        elif c == "}":
            self._add_token(TokenType.RIGHT_BRACE)
        elif c == "[":
            self._add_token(TokenType.LEFT_BRACKET)
        elif c == "]":
            self._add_token(TokenType.RIGHT_BRACKET)
        elif c == ",":
            self._add_token(TokenType.COMMA)
        elif c == ";":
            self._add_token(TokenType.SEMICOLON)
        elif c == "+":
            self._add_token(TokenType.PLUS)
        elif c == "-":
            self._add_token(TokenType.MINUS)
        elif c == "*":
            self._add_token(TokenType.STAR)
        elif c == "/":
            if self._match("/"):
                # commento fino a fine riga
                while self._peek() != "\n" and not self._is_at_end():
                    self._advance()
            else:
                self._add_token(TokenType.SLASH)
        elif c in (" ", "\r", "\t"):
            pass  # spazi ignorati
        elif c == "\n":
            self.line += 1
        elif c == '"':
            self._string()
        elif c.isdigit():
            self._number()
        elif c.isalpha() or c == "_":
            self._identifier()
        else:
            raise LexerError(f"Carattere inatteso: {c!r}", self.line)

    def _string(self) -> None:
        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == "\n":
                self.line += 1
            self._advance()
        if self._is_at_end():
            raise LexerError("Stringa non terminata.", self.line)
        self._advance()  # la " di chiusura
        value = self.source[self.start + 1 : self.current - 1]
        self._add_token(TokenType.STRING, value)

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()
        is_float = False
        if self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()  # il punto
            while self._peek().isdigit():
                self._advance()
        text = self.source[self.start : self.current]
        value = float(text) if is_float else int(text)
        self._add_token(TokenType.NUMBER, value)

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[self.start : self.current]
        type_ = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self._add_token(type_)
