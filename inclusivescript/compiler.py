"""Transpiler InclusiveScript -> Python (primo prototipo di compilatore/traduttore).

Riusa lexer + parser (il front-end) e genera codice Python equivalente.
La parte delicata è preservare la semantica di InclusiveScript:

  - i valori binary king/queen/bi (bi è "falsy");
  - l'accesso sicuro alle liste (fuori range -> nil), gli indici negativi e la
    crescita dinamica;
  - inclusive/exclusive sulle liste;
  - le closure: una funzione annidata che riassegna una variabile del contesto
    esterno richiede `nonlocal` in Python -> facciamo l'analisi degli scope.

Tutto ciò che serve a runtime sta nel PRELUDE, che viene anteposto al programma
tradotto in modo da produrre un file Python autonomo ed eseguibile.
"""

from __future__ import annotations

import keyword
from typing import List, Set

from . import ast_nodes as ast
from .environment import BI
from .tokens import TokenType

# Le funzioni native diventano funzioni del prelude (_isc_*).
NATIVE_MAP = {
    "print": "_isc_print",
    "str": "_isc_str",
    "len": "_isc_len",
    "clock": "_isc_clock",
    "contains": "_isc_contains",
}

PRELUDE = '''\
# -*- coding: utf-8 -*-
# === Runtime InclusiveScript (generato automaticamente) ===
import builtins as _bi
import time as _time


class _Indefinite:
    """Il valore binary indefinito: bi (falsy nelle condizioni)."""
    def __repr__(self):
        return "bi"
    def __bool__(self):
        return False


BI = _Indefinite()


def _isc_stringify(v):
    if v is None:
        return "nil"
    if v is BI:
        return "bi"
    if v is True:
        return "king"
    if v is False:
        return "queen"
    if isinstance(v, float):
        return _bi.str(_bi.int(v)) if v.is_integer() else _bi.str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_isc_elem(x) for x in v) + "]"
    return _bi.str(v)


def _isc_elem(v):
    return '"' + v + '"' if isinstance(v, str) else _isc_stringify(v)


def _isc_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return a == b


def _isc_print(v):
    _bi.print(_isc_stringify(v))
    return None


def _isc_str(v):
    return _isc_stringify(v)


def _isc_len(v):
    if isinstance(v, (str, list)):
        return _bi.len(v)
    raise RuntimeError("len() vuole del testo o una lista.")


def _isc_clock():
    return _time.time()


def _isc_contains(lst, value):
    return _bi.any(_isc_equal(value, x) for x in lst)


def _isc_index_get(coll, index):
    if not isinstance(coll, list):
        raise RuntimeError("Si puo' indicizzare solo una lista.")
    real = index if index >= 0 else _bi.len(coll) + index
    if real < 0 or real >= _bi.len(coll):
        return None
    return coll[real]


def _isc_index_set(coll, index, value):
    if not isinstance(coll, list):
        raise RuntimeError("Si puo' indicizzare solo una lista.")
    if index >= 0:
        real = index
    else:
        real = _bi.len(coll) + index
        if real < 0:
            raise RuntimeError("Indice negativo fuori dai limiti della lista.")
    if real >= _bi.len(coll):
        coll.extend([None] * (real - _bi.len(coll) + 1))
    coll[real] = value
    return value


def _isc_inclusive(coll, value):
    coll.append(value)
    return coll


def _isc_exclusive(coll, value):
    for i, x in enumerate(coll):
        if _isc_equal(value, x):
            coll.pop(i)
            break
    return coll


def _isc_cycle(x):
    if isinstance(x, list):
        for i, v in enumerate(x):
            yield (v, i)
    elif isinstance(x, bool):
        raise RuntimeError("Un cycle vuole una lista o un numero, non un binary.")
    elif isinstance(x, int):
        for i in range(x):
            yield (i, i)
    else:
        raise RuntimeError("Non si puo' ciclare su questo valore: serve una lista o un numero.")


# === Programma tradotto ===
'''


class Transpiler:
    def __init__(self):
        self.lines: List[str] = []
        self.indent = 0
        # Pila degli scope: scopes[0] = globale, poi una per ogni funzione aperta.
        self.scopes: List[Set[str]] = []

    # --- API --------------------------------------------------------------------

    def compile(self, statements: List[ast.Stmt]) -> str:
        self.scopes = [self._collect_locals([], statements)]  # nomi globali
        self.lines = []
        for s in statements:
            self._gen_stmt(s)
        body = "\n".join(self.lines)
        return PRELUDE + ("\n" if not PRELUDE.endswith("\n") else "") + body + "\n"

    # --- utilita' ---------------------------------------------------------------

    def _emit(self, line: str) -> None:
        self.lines.append("    " * self.indent + line)

    @staticmethod
    def _safe(name: str) -> str:
        # Evita le collisioni con le parole chiave di Python.
        return name + "_" if keyword.iskeyword(name) else name

    @staticmethod
    def _as_list(stmt) -> List[ast.Stmt]:
        if isinstance(stmt, ast.Block):
            return stmt.statements
        return [stmt]

    # --- generazione istruzioni -------------------------------------------------

    def _gen_stmt(self, stmt: ast.Stmt) -> None:
        getattr(self, "_gen_" + type(stmt).__name__)(stmt)

    def _gen_FluidStmt(self, stmt: ast.FluidStmt) -> None:
        name = self._safe(stmt.name.lexeme)
        if stmt.initializer is not None:
            self._emit(f"{name} = {self._gen_expr(stmt.initializer)}")
        elif stmt.declared_type == "group":
            self._emit(f"{name} = []")
        elif stmt.declared_type == "binary":
            self._emit(f"{name} = BI")
        else:
            self._emit(f"{name} = None")

    def _gen_ExpressionStmt(self, stmt: ast.ExpressionStmt) -> None:
        e = stmt.expression
        if isinstance(e, ast.Assign):
            self._emit(f"{self._safe(e.name.lexeme)} = {self._gen_expr(e.value)}")
        else:
            self._emit(self._gen_expr(e))

    def _gen_Block(self, stmt: ast.Block) -> None:
        # In Python non esiste lo scope di blocco: avvolgiamo in "if True:".
        self._emit("if True:")
        self._gen_suite(stmt.statements)

    def _gen_If(self, stmt: ast.If) -> None:
        self._emit(f"if {self._gen_expr(stmt.condition)}:")
        self._gen_suite(stmt.then_branch)
        if stmt.else_branch is not None:
            self._emit("else:")
            self._gen_suite(stmt.else_branch)

    def _gen_While(self, stmt: ast.While) -> None:
        self._emit(f"while {self._gen_expr(stmt.condition)}:")
        self._gen_suite(stmt.body)

    def _gen_Cycle(self, stmt: ast.Cycle) -> None:
        item = self._safe(stmt.item.lexeme)
        index = self._safe(stmt.index.lexeme)
        self._emit(f"for {item}, {index} in _isc_cycle({self._gen_expr(stmt.iterable)}):")
        self._gen_suite(stmt.body)

    def _gen_Return(self, stmt: ast.Return) -> None:
        if stmt.value is not None:
            self._emit(f"return {self._gen_expr(stmt.value)}")
        else:
            self._emit("return None")

    def _gen_Function(self, stmt: ast.Function) -> None:
        name = self._safe(stmt.name.lexeme)
        params = ", ".join(self._safe(p.lexeme) for p in stmt.params)
        self._emit(f"def {name}({params}):")
        self.indent += 1

        # Analisi degli scope: quali nomi vanno dichiarati nonlocal / global.
        fn_locals = self._collect_locals(stmt.params, stmt.body)
        assigned = self._collect_assigned(stmt.body)
        free = assigned - fn_locals
        nonlocals = sorted(n for n in free if any(n in s for s in self.scopes[1:]))
        globals_ = sorted(
            n for n in free if n not in nonlocals and n in self.scopes[0]
        )
        for n in nonlocals:
            self._emit(f"nonlocal {self._safe(n)}")
        for n in globals_:
            self._emit(f"global {self._safe(n)}")

        self.scopes.append(fn_locals)
        if stmt.body:
            for s in stmt.body:
                self._gen_stmt(s)
        elif not nonlocals and not globals_:
            self._emit("pass")
        self.scopes.pop()
        self.indent -= 1

    def _gen_suite(self, node) -> None:
        self.indent += 1
        stmts = node if isinstance(node, list) else self._as_list(node)
        if not stmts:
            self._emit("pass")
        else:
            for s in stmts:
                self._gen_stmt(s)
        self.indent -= 1

    # --- generazione espressioni (ritornano stringhe) ---------------------------

    def _gen_expr(self, expr: ast.Expr) -> str:
        return getattr(self, "_gen_" + type(expr).__name__)(expr)

    def _gen_Literal(self, e: ast.Literal) -> str:
        v = e.value
        if v is None:
            return "None"
        if v is BI:
            return "BI"
        if v is True:
            return "True"
        if v is False:
            return "False"
        return repr(v)  # numeri e stringhe

    def _gen_Variable(self, e: ast.Variable) -> str:
        name = e.name.lexeme
        if name in NATIVE_MAP:
            return NATIVE_MAP[name]
        return self._safe(name)

    def _gen_Assign(self, e: ast.Assign) -> str:
        # Assign come sotto-espressione: usa l'operatore walrus.
        return f"({self._safe(e.name.lexeme)} := {self._gen_expr(e.value)})"

    def _gen_Grouping(self, e: ast.Grouping) -> str:
        return f"({self._gen_expr(e.expression)})"

    def _gen_Unary(self, e: ast.Unary) -> str:
        right = self._gen_expr(e.right)
        if e.operator.type == TokenType.MINUS:
            return f"(-{right})"
        return f"(not {right})"  # BANG / not

    def _gen_Binary(self, e: ast.Binary) -> str:
        op = e.operator.type
        left = self._gen_expr(e.left)
        right = self._gen_expr(e.right)
        if op == TokenType.EQUAL_EQUAL:
            return f"_isc_equal({left}, {right})"
        if op == TokenType.BANG_EQUAL:
            return f"(not _isc_equal({left}, {right}))"
        symbol = {
            TokenType.PLUS: "+",
            TokenType.MINUS: "-",
            TokenType.STAR: "*",
            TokenType.SLASH: "/",
            TokenType.GREATER: ">",
            TokenType.GREATER_EQUAL: ">=",
            TokenType.LESS: "<",
            TokenType.LESS_EQUAL: "<=",
        }[op]
        return f"({left} {symbol} {right})"

    def _gen_Logical(self, e: ast.Logical) -> str:
        word = "and" if e.operator.type == TokenType.AND else "or"
        return f"({self._gen_expr(e.left)} {word} {self._gen_expr(e.right)})"

    def _gen_Call(self, e: ast.Call) -> str:
        callee = self._gen_expr(e.callee)
        args = ", ".join(self._gen_expr(a) for a in e.arguments)
        return f"{callee}({args})"

    def _gen_ListLiteral(self, e: ast.ListLiteral) -> str:
        return "[" + ", ".join(self._gen_expr(el) for el in e.elements) + "]"

    def _gen_IndexGet(self, e: ast.IndexGet) -> str:
        return f"_isc_index_get({self._gen_expr(e.collection)}, {self._gen_expr(e.index)})"

    def _gen_IndexSet(self, e: ast.IndexSet) -> str:
        return (
            f"_isc_index_set({self._gen_expr(e.collection)}, "
            f"{self._gen_expr(e.index)}, {self._gen_expr(e.value)})"
        )

    def _gen_ListMutate(self, e: ast.ListMutate) -> str:
        fn = "_isc_inclusive" if e.op.type == TokenType.INCLUSIVE else "_isc_exclusive"
        return f"{fn}({self._gen_expr(e.collection)}, {self._gen_expr(e.value)})"

    # --- analisi degli scope ----------------------------------------------------

    def _collect_locals(self, params, stmts: List[ast.Stmt]) -> Set[str]:
        """Nomi locali a una funzione (o al modulo): parametri, dichiarazioni
        `fluid`, variabili di `cycle` e nomi di funzioni annidate. Non scende
        dentro il corpo delle funzioni annidate."""
        names: Set[str] = {p.lexeme for p in params}
        self._scan_locals(stmts, names)
        return names

    def _scan_locals(self, stmts: List[ast.Stmt], names: Set[str]) -> None:
        for s in stmts:
            t = type(s).__name__
            if t == "FluidStmt":
                names.add(s.name.lexeme)
            elif t == "Function":
                names.add(s.name.lexeme)  # il nome è locale; non scendiamo nel corpo
            elif t == "If":
                self._scan_locals(self._as_list(s.then_branch), names)
                if s.else_branch is not None:
                    self._scan_locals(self._as_list(s.else_branch), names)
            elif t == "While":
                self._scan_locals(self._as_list(s.body), names)
            elif t == "Cycle":
                names.add(s.item.lexeme)
                names.add(s.index.lexeme)
                self._scan_locals(s.body, names)
            elif t == "Block":
                self._scan_locals(s.statements, names)

    def _collect_assigned(self, stmts: List[ast.Stmt]) -> Set[str]:
        """Nomi riassegnati (via `feels`) dentro la funzione, senza scendere nelle
        funzioni annidate. Solo le riassegnazioni di variabile contano: le
        mutazioni di lista (indice, inclusive/exclusive) non rilegano il nome."""
        names: Set[str] = set()
        self._scan_assigned(stmts, names)
        return names

    def _scan_assigned(self, stmts: List[ast.Stmt], names: Set[str]) -> None:
        for s in stmts:
            t = type(s).__name__
            if t == "Function":
                continue  # gestisce i propri scope
            elif t == "ExpressionStmt":
                self._scan_expr_assigned(s.expression, names)
            elif t == "Return":
                if s.value is not None:
                    self._scan_expr_assigned(s.value, names)
            elif t == "FluidStmt":
                if s.initializer is not None:
                    self._scan_expr_assigned(s.initializer, names)
            elif t == "If":
                self._scan_expr_assigned(s.condition, names)
                self._scan_assigned(self._as_list(s.then_branch), names)
                if s.else_branch is not None:
                    self._scan_assigned(self._as_list(s.else_branch), names)
            elif t == "While":
                self._scan_expr_assigned(s.condition, names)
                self._scan_assigned(self._as_list(s.body), names)
            elif t == "Cycle":
                self._scan_expr_assigned(s.iterable, names)
                self._scan_assigned(s.body, names)
            elif t == "Block":
                self._scan_assigned(s.statements, names)

    def _scan_expr_assigned(self, e: ast.Expr, names: Set[str]) -> None:
        t = type(e).__name__
        if t == "Assign":
            names.add(e.name.lexeme)
            self._scan_expr_assigned(e.value, names)
        elif t in ("Binary", "Logical"):
            self._scan_expr_assigned(e.left, names)
            self._scan_expr_assigned(e.right, names)
        elif t == "Unary":
            self._scan_expr_assigned(e.right, names)
        elif t == "Grouping":
            self._scan_expr_assigned(e.expression, names)
        elif t == "Call":
            self._scan_expr_assigned(e.callee, names)
            for a in e.arguments:
                self._scan_expr_assigned(a, names)
        elif t == "ListLiteral":
            for el in e.elements:
                self._scan_expr_assigned(el, names)
        elif t == "IndexGet":
            self._scan_expr_assigned(e.collection, names)
            self._scan_expr_assigned(e.index, names)
        elif t == "IndexSet":
            self._scan_expr_assigned(e.collection, names)
            self._scan_expr_assigned(e.index, names)
            self._scan_expr_assigned(e.value, names)
        elif t == "ListMutate":
            self._scan_expr_assigned(e.collection, names)
            self._scan_expr_assigned(e.value, names)


def transpile(statements: List[ast.Stmt]) -> str:
    """Funzione di comodo: AST -> sorgente Python."""
    return Transpiler().compile(statements)
