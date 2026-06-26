"""Interprete tree-walking di InclusiveScript.

Visita l'AST ed esegue il programma.
"""

from __future__ import annotations

import time
from typing import Any, List

from . import ast_nodes as ast
from .environment import BI, Environment, infer_type, kind_of
from .errors import RuntimeError_
from .tokens import Token, TokenType


class ReturnException(Exception):
    """Usata internamente per implementare 'return' risalendo lo stack."""

    def __init__(self, value: Any):
        super().__init__()
        self.value = value


class Callable:
    """Interfaccia per tutto cio' che e' invocabile."""

    def arity(self) -> int:
        raise NotImplementedError

    def call(self, interpreter: "Interpreter", arguments: List[Any]) -> Any:
        raise NotImplementedError


class NativeFunction(Callable):
    def __init__(self, name: str, arity: int, fn):
        self.name = name
        self._arity = arity
        self.fn = fn

    def arity(self) -> int:
        return self._arity

    def call(self, interpreter: "Interpreter", arguments: List[Any]) -> Any:
        return self.fn(*arguments)

    def __str__(self) -> str:
        return f"<funzione nativa {self.name}>"


class InclusiveFunction(Callable):
    def __init__(self, declaration: ast.Function, closure: Environment):
        self.declaration = declaration
        self.closure = closure

    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter: "Interpreter", arguments: List[Any]) -> Any:
        environment = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, arg)
        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnException as r:
            return r.value
        return None

    def __str__(self) -> str:
        return f"<funzione {self.declaration.name.lexeme}>"


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals
        self._install_natives()

    def _install_natives(self) -> None:
        def _print(value):
            print(stringify(value))
            return None

        def _len(v):
            if isinstance(v, (str, list)):
                return len(v)
            raise RuntimeError_("len() vuole del testo o una lista.", 0)

        def _contains(lst, value):
            _check_list(lst, "contains")
            return any(is_equal(value, x) for x in lst)

        self.globals.define("print", NativeFunction("print", 1, _print))
        self.globals.define("clock", NativeFunction("clock", 0, lambda: time.time()))
        self.globals.define("str", NativeFunction("str", 1, lambda v: stringify(v)))
        self.globals.define("len", NativeFunction("len", 1, _len))
        self.globals.define("contains", NativeFunction("contains", 2, _contains))

    # --- punto di ingresso -------------------------------------------------------

    def interpret(self, statements: List[ast.Stmt]) -> None:
        for statement in statements:
            self._execute(statement)

    # --- esecuzione istruzioni ---------------------------------------------------

    def _execute(self, stmt: ast.Stmt) -> None:
        method = getattr(self, "_exec_" + type(stmt).__name__)
        method(stmt)

    def _exec_ExpressionStmt(self, stmt: ast.ExpressionStmt) -> None:
        self._evaluate(stmt.expression)

    def _exec_FluidStmt(self, stmt: ast.FluidStmt) -> None:
        declared_type = stmt.declared_type
        if stmt.initializer is not None:
            value = self._evaluate(stmt.initializer)
            if declared_type is None:
                declared_type = infer_type(value)  # tipo dedotto dal valore
        elif declared_type == "group":
            value = []          # una group senza valore nasce come lista vuota
        elif declared_type == "binary":
            value = BI          # un binary non ancora deciso e' indefinito (bi)
        else:
            value = None        # nonbinary (o tipo non deducibile) senza valore = nil
            declared_type = "nonbinary"
        self.environment.define(
            stmt.name.lexeme, value, declared_type, stmt.name.line
        )

    def _exec_Block(self, stmt: ast.Block) -> None:
        self.execute_block(stmt.statements, Environment(self.environment))

    def execute_block(self, statements: List[ast.Stmt], environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous

    def _exec_If(self, stmt: ast.If) -> None:
        if is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute(stmt.else_branch)

    def _exec_While(self, stmt: ast.While) -> None:
        while is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.body)

    def _exec_Cycle(self, stmt: ast.Cycle) -> None:
        iterable = self._evaluate(stmt.iterable)

        if isinstance(iterable, list):
            # itera la lista: item = elemento, index = posizione
            pairs = list(enumerate(iterable))
        elif isinstance(iterable, bool):
            raise RuntimeError_(
                "Un cycle vuole una lista o un numero, non un binary.", stmt.item.line
            )
        elif isinstance(iterable, int):
            if iterable < 0:
                raise RuntimeError_(
                    "Un cycle su un numero richiede un intero non negativo.", stmt.item.line
                )
            # ripete N volte: item e index coincidono (0 .. N-1)
            pairs = [(i, i) for i in range(iterable)]
        else:
            raise RuntimeError_(
                f"Non si puo' ciclare su un {kind_of(iterable)}: serve una lista o un numero.",
                stmt.item.line,
            )

        for idx, value in pairs:
            # scope fresco a ogni giro: item e index sono variabili senza tipo
            loop_env = Environment(self.environment)
            loop_env.define(stmt.item.lexeme, value)
            loop_env.define(stmt.index.lexeme, idx)
            self.execute_block(stmt.body, loop_env)

    def _exec_Function(self, stmt: ast.Function) -> None:
        function = InclusiveFunction(stmt, self.environment)
        self.environment.define(stmt.name.lexeme, function)

    def _exec_Return(self, stmt: ast.Return) -> None:
        value = None
        if stmt.value is not None:
            value = self._evaluate(stmt.value)
        raise ReturnException(value)

    # --- valutazione espressioni -------------------------------------------------

    def _evaluate(self, expr: ast.Expr) -> Any:
        method = getattr(self, "_eval_" + type(expr).__name__)
        return method(expr)

    def _eval_Literal(self, expr: ast.Literal) -> Any:
        return expr.value

    def _eval_Grouping(self, expr: ast.Grouping) -> Any:
        return self._evaluate(expr.expression)

    def _eval_Variable(self, expr: ast.Variable) -> Any:
        return self.environment.get(expr.name)

    def _eval_Assign(self, expr: ast.Assign) -> Any:
        value = self._evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def _eval_Unary(self, expr: ast.Unary) -> Any:
        right = self._evaluate(expr.right)
        op = expr.operator.type
        if op == TokenType.MINUS:
            _check_number(expr.operator, right)
            return -right
        if op == TokenType.BANG:
            return not is_truthy(right)
        return None  # irraggiungibile

    def _eval_Logical(self, expr: ast.Logical) -> Any:
        left = self._evaluate(expr.left)
        if expr.operator.type == TokenType.OR:
            if is_truthy(left):
                return left
        else:  # AND
            if not is_truthy(left):
                return left
        return self._evaluate(expr.right)

    def _eval_Binary(self, expr: ast.Binary) -> Any:
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        op = expr.operator.type

        if op == TokenType.PLUS:
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            raise RuntimeError_(
                "Gli operandi di '+' devono essere entrambi numeri o entrambe stringhe.",
                expr.operator.line,
            )
        if op == TokenType.MINUS:
            _check_numbers(expr.operator, left, right)
            return left - right
        if op == TokenType.STAR:
            _check_numbers(expr.operator, left, right)
            return left * right
        if op == TokenType.SLASH:
            _check_numbers(expr.operator, left, right)
            if right == 0:
                raise RuntimeError_("Divisione per zero.", expr.operator.line)
            return left / right
        if op == TokenType.GREATER:
            _check_numbers(expr.operator, left, right)
            return left > right
        if op == TokenType.GREATER_EQUAL:
            _check_numbers(expr.operator, left, right)
            return left >= right
        if op == TokenType.LESS:
            _check_numbers(expr.operator, left, right)
            return left < right
        if op == TokenType.LESS_EQUAL:
            _check_numbers(expr.operator, left, right)
            return left <= right
        if op == TokenType.EQUAL_EQUAL:
            return is_equal(left, right)
        if op == TokenType.BANG_EQUAL:
            return not is_equal(left, right)
        return None  # irraggiungibile

    def _eval_Call(self, expr: ast.Call) -> Any:
        callee = self._evaluate(expr.callee)
        arguments = [self._evaluate(arg) for arg in expr.arguments]
        if not isinstance(callee, Callable):
            raise RuntimeError_("Si possono chiamare solo funzioni.", expr.paren.line)
        if len(arguments) != callee.arity():
            raise RuntimeError_(
                f"Attesi {callee.arity()} argomenti ma ricevuti {len(arguments)}.",
                expr.paren.line,
            )
        return callee.call(self, arguments)

    def _eval_ListLiteral(self, expr: ast.ListLiteral) -> Any:
        return [self._evaluate(e) for e in expr.elements]

    def _eval_IndexGet(self, expr: ast.IndexGet) -> Any:
        collection = self._evaluate(expr.collection)
        index = self._index_value(self._evaluate(expr.index), expr.bracket)
        if not isinstance(collection, list):
            raise RuntimeError_(
                f"Si puo' indicizzare solo una lista (ricevuto un {kind_of(collection)}).",
                expr.bracket.line,
            )
        real = index if index >= 0 else len(collection) + index
        # Accesso sicuro: fuori dai limiti -> nil, niente crash.
        if real < 0 or real >= len(collection):
            return None
        return collection[real]

    def _eval_IndexSet(self, expr: ast.IndexSet) -> Any:
        collection = self._evaluate(expr.collection)
        index = self._index_value(self._evaluate(expr.index), expr.bracket)
        value = self._evaluate(expr.value)
        if not isinstance(collection, list):
            raise RuntimeError_(
                f"Si puo' indicizzare solo una lista (ricevuto un {kind_of(collection)}).",
                expr.bracket.line,
            )
        if index >= 0:
            real = index
        else:
            real = len(collection) + index
            if real < 0:
                raise RuntimeError_(
                    "Indice negativo fuori dai limiti della lista.", expr.bracket.line
                )
        # Crescita dinamica: oltre la fine, la lista si allunga riempiendo con nil.
        if real >= len(collection):
            collection.extend([None] * (real - len(collection) + 1))
        collection[real] = value
        return value

    def _eval_ListMutate(self, expr: ast.ListMutate) -> Any:
        collection = self._evaluate(expr.collection)
        value = self._evaluate(expr.value)
        if not isinstance(collection, list):
            raise RuntimeError_(
                f"'{expr.op.lexeme}' funziona solo su una lista (group), "
                f"non su un {kind_of(collection)}.",
                expr.op.line,
            )
        if expr.op.type == TokenType.INCLUSIVE:
            collection.append(value)
        else:  # EXCLUSIVE: toglie la prima occorrenza, se presente
            for i, x in enumerate(collection):
                if is_equal(value, x):
                    collection.pop(i)
                    break
        return collection

    @staticmethod
    def _index_value(index: Any, bracket) -> int:
        if isinstance(index, bool) or not isinstance(index, int):
            raise RuntimeError_(
                "L'indice di una lista deve essere un numero intero.", bracket.line
            )
        return index


# === Funzioni di supporto ===================================================


def is_truthy(value: Any) -> bool:
    """Falsi: nil, queen (false) e bi (indefinito). Tutto il resto e' vero."""
    if value is None:
        return False
    if value is BI:
        return False
    if isinstance(value, bool):
        return value
    return True


def is_equal(a: Any, b: Any) -> bool:
    # Evita che True == 1 sia vero (in Python lo sarebbe)
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return a == b


def _check_number(operator: Token, operand: Any) -> None:
    if not isinstance(operand, (int, float)) or isinstance(operand, bool):
        raise RuntimeError_("L'operando deve essere un numero.", operator.line)


def _check_numbers(operator: Token, left: Any, right: Any) -> None:
    ok_left = isinstance(left, (int, float)) and not isinstance(left, bool)
    ok_right = isinstance(right, (int, float)) and not isinstance(right, bool)
    if not (ok_left and ok_right):
        raise RuntimeError_("Gli operandi devono essere numeri.", operator.line)


def _check_list(value: Any, fn_name: str) -> None:
    if not isinstance(value, list):
        raise RuntimeError_(f"{fn_name}() vuole una lista come primo argomento.", 0)


def stringify(value: Any) -> str:
    if value is None:
        return "nil"
    if value is BI:
        return "bi"
    if isinstance(value, bool):
        return "king" if value else "queen"
    if isinstance(value, float):
        # Mostra gli interi senza decimale superfluo: 5.0 -> "5"
        if value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_stringify_element(x) for x in value) + "]"
    return str(value)


def _stringify_element(value: Any) -> str:
    """Come stringify, ma il testo dentro una lista viene mostrato tra virgolette."""
    if isinstance(value, str):
        return '"' + value + '"'
    return stringify(value)
