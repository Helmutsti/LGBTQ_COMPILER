"""Definizione dei token di InclusiveScript."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    # Simboli a un carattere
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    # Simboli a uno o due caratteri
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    # Letterali
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Parole chiave
    FLUID = auto()
    BINARY = auto()
    NONBINARY = auto()
    GROUP = auto()
    FEELS = auto()
    INCLUSIVE = auto()
    EXCLUSIVE = auto()
    BE = auto()
    FUN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    CYCLE = auto()
    IN = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    BI = auto()
    NIL = auto()
    AND = auto()
    OR = auto()

    EOF = auto()


# Mappa parola chiave -> tipo di token
KEYWORDS = {
    "fluid": TokenType.FLUID,
    "binary": TokenType.BINARY,
    "nonbinary": TokenType.NONBINARY,
    "group": TokenType.GROUP,
    "feels": TokenType.FEELS,
    "inclusive": TokenType.INCLUSIVE,
    "exclusive": TokenType.EXCLUSIVE,
    "be": TokenType.BE,
    "fun": TokenType.FUN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "cycle": TokenType.CYCLE,
    "in": TokenType.IN,
    "return": TokenType.RETURN,
    "king": TokenType.TRUE,    # valore binary "si'"
    "queen": TokenType.FALSE,  # valore binary "no"
    "bi": TokenType.BI,        # valore binary "indefinito"
    "nil": TokenType.NIL,
    "and": TokenType.AND,
    "or": TokenType.OR,
    # Operatori "a parole" (mappati ai tipi di token esistenti)
    "likes": TokenType.EQUAL_EQUAL,         # ==
    "unlikes": TokenType.BANG_EQUAL,        # !=
    "under": TokenType.LESS,                # <
    "underlikes": TokenType.LESS_EQUAL,     # <=
    "over": TokenType.GREATER,              # >
    "overlikes": TokenType.GREATER_EQUAL,   # >=
    "not": TokenType.BANG,                  # !  (negazione logica)
}


@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    line: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.lexeme!r}, {self.literal!r})"
