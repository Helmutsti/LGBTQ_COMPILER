#!/usr/bin/env python3
"""InclusiveScript - entry point.

Uso:
    python isc.py                       # avvia la REPL interattiva
    python isc.py file.lgbtq            # esegue un file sorgente (interprete)
    python isc.py --compile file.lgbtq            # traduce in Python su stdout
    python isc.py --compile file.lgbtq out.py     # traduce in Python e scrive su file
"""

from __future__ import annotations

import sys

from inclusivescript.compiler import transpile
from inclusivescript.errors import InclusiveError, LexerError, ParseError, RuntimeError_
from inclusivescript.interpreter import Interpreter
from inclusivescript.lexer import Lexer
from inclusivescript.parser import Parser


def _parse(source: str):
    """Sorgente -> AST (lexer + parser)."""
    tokens = Lexer(source).scan_tokens()
    return Parser(tokens).parse()


def run(source: str, interpreter: Interpreter) -> bool:
    """Esegue il sorgente. Ritorna True in caso di successo, False se c'e' stato un errore."""
    try:
        interpreter.interpret(_parse(source))
        return True
    except (LexerError, ParseError) as e:
        print(f"Errore di sintassi {e}", file=sys.stderr)
        return False
    except RuntimeError_ as e:
        print(f"Errore a runtime {e}", file=sys.stderr)
        return False
    except InclusiveError as e:
        print(f"Errore {e}", file=sys.stderr)
        return False


def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except OSError as e:
        print(f"Impossibile aprire il file: {e}", file=sys.stderr)
        sys.exit(74)


def run_file(path: str) -> None:
    interpreter = Interpreter()
    ok = run(_read_file(path), interpreter)
    if not ok:
        sys.exit(65)


def compile_file(path: str, out_path: str | None) -> None:
    """Traduce un file InclusiveScript in Python."""
    source = _read_file(path)
    try:
        python_code = transpile(_parse(source))
    except (LexerError, ParseError) as e:
        print(f"Errore di sintassi {e}", file=sys.stderr)
        sys.exit(65)
    if out_path is None:
        sys.stdout.write(python_code)
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(python_code)
        print(f"Tradotto in Python: {out_path}", file=sys.stderr)


def run_repl() -> None:
    print("InclusiveScript REPL - scrivi 'exit' o Ctrl+C per uscire.")
    interpreter = Interpreter()  # stato condiviso tra le righe
    while True:
        try:
            line = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip() in ("exit", "quit"):
            break
        if not line.strip():
            continue
        run(line, interpreter)


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] in ("--compile", "--to-python", "-c"):
        rest = args[1:]
        if not rest or len(rest) > 2:
            print("Uso: python isc.py --compile file.lgbtq [out.py]", file=sys.stderr)
            sys.exit(64)
        compile_file(rest[0], rest[1] if len(rest) == 2 else None)
    elif len(args) > 1:
        print("Uso: python isc.py [--compile] file.lgbtq [out.py]", file=sys.stderr)
        sys.exit(64)
    elif len(args) == 1:
        run_file(args[0])
    else:
        run_repl()


if __name__ == "__main__":
    main()
