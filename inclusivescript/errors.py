"""Errori del linguaggio InclusiveScript."""

from __future__ import annotations


class InclusiveError(Exception):
    """Errore base con riga sorgente."""

    def __init__(self, message: str, line: int):
        super().__init__(message)
        self.message = message
        self.line = line

    def __str__(self) -> str:
        return f"[riga {self.line}] {self.message}"


class LexerError(InclusiveError):
    """Errore durante la tokenizzazione."""


class ParseError(InclusiveError):
    """Errore durante il parsing."""


class RuntimeError_(InclusiveError):
    """Errore durante l'esecuzione (a runtime)."""
