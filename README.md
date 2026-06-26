# InclusiveScript

Un piccolo linguaggio di programmazione imperativo, con **interprete tree-walking**
e **transpiler verso Python**, scritto in Python.

> Il nome "InclusiveScript" è provvisorio.

## Avvio rapido

```bash
# Esegui un file (interprete)
python isc.py examples/esempio.lgbtq

# Avvia la REPL interattiva
python isc.py

# Traduci in Python (compilatore/traduttore)
python isc.py --compile examples/esempio.lgbtq           # stampa il Python su stdout
python isc.py --compile examples/esempio.lgbtq out.py    # oppure scrive su file
python out.py                                          # il risultato è eseguibile
```

> Su questa macchina puoi usare il Python locale: `~\python\python.exe isc.py examples\esempio.lgbtq`

## Il linguaggio

Vedi il **[MANIFESTO.md](MANIFESTO.md)** per la filosofia e le regole dei tipi.

```js
// Tipi: binary (king/queen/bi), nonbinary (testo/numeri/funzioni), group (liste).
// Il tipo è opzionale (inferito dal valore) e il ';' anche.
fluid nome feels "Manuel"     // inferito: nonbinary (testo)
fluid x feels 10              // inferito: nonbinary (numero)
fluid binary attivo feels king

// Assegnazione con 'feels'
x feels x + 5

// if implicito: condizione + cuori (niente 'if' né parentesi)
// invocazione con 'be' (senza parentesi); 'print' è una funzione di sistema
x over 5 and attivo ❤️
  be print "grande"
💔 else ❤️
  be print "piccolo"
💔

// Funzioni con return e ricorsione (forma classica con { } e ; ancora valida)
fun fattoriale(n) {
  if (n underlikes 1) { return 1; }
  return n * fattoriale(n - 1);
}
print(fattoriale(5));   // 120

fluid i feels 0
while (i under 3) {
  print(i);
  i feels i + 1;
}

// Liste inclusive (group) + cycle (i cuori ❤️ 💔 sono le graffe)
fluid group nomi feels ["Manuel", "Sara", "Luca"];
nomi inclusive "Ada";     // aggiungi
nomi exclusive "Sara";    // togli
cycle(persona, pos in nomi) ❤️
  print(str(pos) + ": " + persona);
💔
print(nomi[-1]);   // Ada (indice negativo)
print(nomi[99]);   // nil (accesso sicuro)
```

### Caratteristiche attuali
- Tipi (con controllo): `binary` (`king`/`queen`/`bi`), `nonbinary` (testo/numeri/funzioni), `group` (liste)
- Dichiarazione con `fluid [tipo] <nome>`: **tipo opzionale** (se assente, inferito dal valore), assegnazione con `feels`
- **`;` opzionale** (puoi terminare con `;` o andare a capo)
- Operatori aritmetici: `+ - * /` (`+` concatena anche il testo)
- Confronti/logici **a parole**: `likes` (==), `unlikes` (!=), `under` (<), `underlikes` (<=), `over` (>), `overlikes` (>=), `not`, `and`, `or`
- Condizioni: **`if` implicito** (`<cond> ❤️ … 💔 [else …]`) oppure classico `if (<cond>) { … }`; `while` e `cycle` (`cycle(item, index in lista|numero)`)
- **Liste inclusive** (`fluid group`, letterale `[...]`): unica struttura dati, con accesso sicuro (fuori range → `nil`), indici negativi e crescita dinamica; aggiungi/togli con `lista inclusive v` / `lista exclusive v`
- Funzioni (`fun`), `return`, ricorsione e **closure**; una funzione è un valore (`nonbinary`)
- Invocazione: `nome(arg)` **oppure** con `be` senza parentesi — `be print "ciao"`, `be somma 3, 4`
- Blocchi con `{ }` **oppure** con i cuori `❤️` … `💔`
- Commenti con `//`
- Funzioni native: `print`, `clock`, `str`, `len`, `contains`

## Architettura

Il front-end (lexer + parser) è condiviso da due back-end: l'interprete e il
transpiler verso Python.

```
                                   ┌→ [Interpreter] → esecuzione
sorgente → [Lexer] → token → [Parser] → AST ┤
                                   └→ [Compiler] → sorgente Python
```

| File | Ruolo |
|------|-------|
| `inclusivescript/tokens.py`      | Tipi di token e parole chiave |
| `inclusivescript/lexer.py`       | Tokenizzatore (testo → token) |
| `inclusivescript/ast_nodes.py`   | Nodi dell'Abstract Syntax Tree |
| `inclusivescript/parser.py`      | Parser a discesa ricorsiva (token → AST) |
| `inclusivescript/environment.py` | Tabella dei simboli, scope annidati e controllo dei tipi |
| `inclusivescript/interpreter.py` | Interprete tree-walking (esegue l'AST) |
| `inclusivescript/compiler.py`    | **Transpiler AST → Python** (con analisi degli scope per `nonlocal`) |
| `inclusivescript/errors.py`      | Errori con numero di riga |
| `isc.py`                         | Entry point: REPL, esecuzione e `--compile` |

### Il transpiler (primo prototipo di compilatore)

`--compile` traduce InclusiveScript in **Python autonomo ed eseguibile**. Il file
generato comincia con un piccolo *runtime* (`_isc_*`) che preserva la semantica del
linguaggio: i valori `king`/`queen`/`bi` (con `bi` "falsy"), l'accesso sicuro alle
liste, gli indici negativi, la crescita dinamica e `inclusive`/`exclusive`. Le
**closure** sono tradotte correttamente grazie a un'analisi degli scope che inserisce
le dichiarazioni `nonlocal`/`global` dove servono.

Output dell'interprete e del Python tradotto **coincidono** sull'esempio.

## Idee per i prossimi passi
- Compilatore: opzione `--run` per tradurre ed eseguire al volo; emissione di `break`/`continue`
- `cycle` con un solo nome quando l'indice non serve
- Altri poteri delle liste: ordinamento, slicing, `map`/`filter`
- Conversioni tra tipi (numero ↔ testo)
- Suite di test automatici (confronto interprete ↔ Python tradotto)
