"""Nodi dell'Abstract Syntax Tree (AST) di InclusiveScript."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from .tokens import Token


# === Espressioni ============================================================


class Expr:
    """Classe base per le espressioni."""


@dataclass
class Literal(Expr):
    value: Any


@dataclass
class Grouping(Expr):
    expression: Expr


@dataclass
class Variable(Expr):
    name: Token


@dataclass
class Assign(Expr):
    name: Token
    value: Expr


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class Call(Expr):
    callee: Expr
    paren: Token  # parentesi di chiusura, per i messaggi d'errore
    arguments: List[Expr]


@dataclass
class ListLiteral(Expr):
    elements: List[Expr]


@dataclass
class IndexGet(Expr):
    collection: Expr
    bracket: Token  # '[' per i messaggi d'errore
    index: Expr


@dataclass
class IndexSet(Expr):
    collection: Expr
    bracket: Token
    index: Expr
    value: Expr


@dataclass
class ListMutate(Expr):
    collection: Expr
    op: Token         # 'inclusive' (aggiunge) oppure 'exclusive' (rimuove)
    value: Expr


# === Istruzioni =============================================================


class Stmt:
    """Classe base per le istruzioni."""


@dataclass
class ExpressionStmt(Stmt):
    expression: Expr


@dataclass
class FluidStmt(Stmt):
    name: Token
    declared_type: Optional[str]  # "binary"/"nonbinary"/"group", oppure None = da inferire
    initializer: Optional[Expr]


@dataclass
class Block(Stmt):
    statements: List[Stmt]


@dataclass
class If(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]


@dataclass
class While(Stmt):
    condition: Expr
    body: Stmt


@dataclass
class Cycle(Stmt):
    item: Token       # variabile dell'elemento corrente
    index: Token      # variabile della posizione corrente
    iterable: Expr    # lista oppure intero (numero di ripetizioni)
    body: List[Stmt]


@dataclass
class Function(Stmt):
    name: Token
    params: List[Token]
    body: List[Stmt]


@dataclass
class Return(Stmt):
    keyword: Token
    value: Optional[Expr]
