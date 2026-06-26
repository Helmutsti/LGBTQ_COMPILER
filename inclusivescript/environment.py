"""Ambiente (tabella dei simboli) con scope annidati e controllo dei tipi.

Ogni variabile dichiarata con 'fluid' porta con se' un tipo:
  - "binary"     -> puo' contenere solo true / false
  - "nonbinary"  -> puo' contenere testo (stringa) oppure numeri (int/float)

Il valore nil (None) e' sempre ammesso: rappresenta una variabile non ancora
"definita" con un valore concreto.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .errors import RuntimeError_
from .tokens import Token


class _Indefinite:
    """Il valore binary 'indefinito': bi. Singleton, distinto da king/queen e da nil."""

    def __repr__(self) -> str:
        return "bi"


# Unica istanza condivisa: rappresenta il valore 'bi' a runtime.
BI = _Indefinite()


def is_binary_value(value: Any) -> bool:
    """king/queen (bool) oppure bi: i tre valori del tipo binary."""
    return isinstance(value, bool) or value is BI


def infer_type(value: Any) -> str:
    """Deduce il tipo di una variabile 'fluid' senza tipo, dal suo valore.

    king/queen/bi -> binary; una lista -> group; tutto il resto -> nonbinary
    (testo, numeri, funzioni e anche nil, che resta liberamente assegnabile).
    """
    if is_binary_value(value):
        return "binary"
    if isinstance(value, list):
        return "group"
    return "nonbinary"


def kind_of(value: Any) -> str:
    """Nome leggibile del 'genere' di un valore, per i messaggi d'errore."""
    if value is None:
        return "nil"
    if value is BI:
        return "binary (bi)"
    if isinstance(value, bool):
        return "binary"
    if isinstance(value, str):
        return "nonbinary (testo)"
    if isinstance(value, (int, float)):
        return "nonbinary (numero)"
    if isinstance(value, list):
        return "group (lista)"
    if hasattr(value, "call") and hasattr(value, "arity"):
        return "nonbinary (funzione)"
    return type(value).__name__


def check_type(declared_type: Optional[str], value: Any, name: str, line: int) -> None:
    """Verifica che 'value' sia compatibile con il tipo dichiarato.

    Tassonomia dei tipi (a tema):
      - binary    -> king / queen / bi (i tre stati);
      - group     -> una lista (la struttura dati inclusiva);
      - nonbinary -> tutto il resto (testo, numeri, funzioni).

    declared_type None significa "senza tipo" (es. parametri di funzione e
    variabili di cycle): nessun controllo. Il valore nil e' sempre accettato.
    """
    if declared_type is None or value is None:
        return

    if declared_type == "binary":
        if not is_binary_value(value):
            raise RuntimeError_(
                f"La variabile binary '{name}' accetta solo king, queen o bi, "
                f"ma ha ricevuto un {kind_of(value)}.",
                line,
            )
    elif declared_type == "group":
        if not isinstance(value, list):
            raise RuntimeError_(
                f"La variabile group '{name}' accetta solo una lista, "
                f"ma ha ricevuto un {kind_of(value)}.",
                line,
            )
    elif declared_type == "nonbinary":
        if is_binary_value(value):
            raise RuntimeError_(
                f"La variabile nonbinary '{name}' non accetta valori binary "
                f"(king/queen/bi): quello e' territorio del binary.",
                line,
            )
        if isinstance(value, list):
            raise RuntimeError_(
                f"La variabile nonbinary '{name}' non accetta una lista: "
                f"usa il tipo 'group'.",
                line,
            )


class Environment:
    def __init__(self, enclosing: Optional["Environment"] = None):
        self.values: Dict[str, Any] = {}
        self.types: Dict[str, Optional[str]] = {}
        self.enclosing = enclosing

    def define(
        self, name: str, value: Any, declared_type: Optional[str] = None, line: int = 0
    ) -> None:
        """Definisce una variabile nello scope corrente, validandone il tipo."""
        check_type(declared_type, value, name, line)
        self.values[name] = value
        self.types[name] = declared_type

    def get(self, name: Token) -> Any:
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        if self.enclosing is not None:
            return self.enclosing.get(name)
        raise RuntimeError_(f"Variabile non definita '{name.lexeme}'.", name.line)

    def assign(self, name: Token, value: Any) -> None:
        if name.lexeme in self.values:
            check_type(self.types.get(name.lexeme), value, name.lexeme, name.line)
            self.values[name.lexeme] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise RuntimeError_(f"Variabile non definita '{name.lexeme}'.", name.line)
