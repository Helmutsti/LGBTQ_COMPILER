# Il Manifesto di InclusiveScript

> *Un linguaggio in cui i dati non vengono incasellati a forza, ma dichiarati per ciò che sono.*

InclusiveScript nasce da un'idea semplice: il sistema dei tipi di un linguaggio di
programmazione è, in fondo, un modo di **classificare**. InclusiveScript prende quella
classificazione e la riscrive con un vocabolario che parla di identità, fluidità e
rispetto. Le parole chiave non sono un travestimento: sono il cuore del linguaggio.

Il nome è ancora provvisorio. La filosofia, no.

## I file

Un programma InclusiveScript vive in un file con estensione **`.lgbtq`**. È l'unica
estensione riconosciuta: i sorgenti del linguaggio si scrivono e si eseguono come
file `*.lgbtq` (per esempio `myprogram.lgbtq`).

---

## 1. I tipi

InclusiveScript ha tre tipi: `binary`, `nonbinary` e `group` (le liste, con una
sezione dedicata più avanti).

### `binary` — il tipo a tre stati

Una variabile `binary` può assumere **tre valori**:

- `king` — sì / vero;
- `queen` — no / falso;
- `bi` — **indefinito**: né l'uno né l'altro, non ancora deciso.

`king` e `queen` sono i due stati definiti; `bi` è lo stato fluido che rifiuta la
dicotomia. Un `binary` dichiarato senza valore nasce proprio come `bi`.

```js
fluid binary attivo feels king;
fluid binary completato feels queen;
fluid binary indeciso;           // vale bi
```

Nelle condizioni solo `king` conta come vero: `queen` e `bi` sono "non veri".

Assegnare a un `binary` qualcosa che non sia `king`, `queen` o `bi` è un errore:

```js
fluid binary x feels 5;
// Errore a runtime: La variabile binary 'x' accetta solo king, queen o bi,
// ma ha ricevuto un nonbinary (numero).
```

### `nonbinary` — il tipo che non si lascia incasellare

Una variabile `nonbinary` rifiuta la dicotomia: può contenere **tutto ciò che non
è `binary`**. Il caso più comune è il **testo** o un **numero**, e il "sotto-genere"
si rivela dal modo in cui viene definita:

- definita con le virgolette `"..."` → è **testo** (una stringa);
- definita senza virgolette, con cifre → è un **numero** (intero o decimale).

```js
fluid nonbinary nome feels "Manuel";   // "" presenti  -> testo
fluid nonbinary eta  feels 32;         // niente ""     -> numero intero
fluid nonbinary pi   feels 3.14;       // niente ""     -> numero decimale
```

Oltre a testo e numeri, un `nonbinary` accoglie anche le **funzioni**: sono valori
di prima classe come gli altri.

```js
fluid nonbinary azione feels saluta;   // una funzione
```

Un `nonbinary` rifiuta i valori `binary` (`king`/`queen`/`bi`) — quello è territorio
del `binary` — e rifiuta le **liste**, che hanno il loro tipo dedicato, `group`.

```js
fluid nonbinary y feels king;
// Errore a runtime: La variabile nonbinary 'y' non accetta valori binary
// (king/queen/bi): quello e' territorio del binary.
```

---

## 2. Dichiarare: `fluid`

Ogni variabile entra nel mondo attraverso la parola `fluid`. Il tipo è **opzionale**:
se lo ometti, viene **inferito** dal valore iniziale.

```
fluid <tipo> <nome>                       // tipo esplicito
fluid <tipo> <nome> feels <valore>
fluid <nome> feels <valore>               // tipo inferito dal valore
```

```js
fluid a feels 10;                 // inferito: nonbinary (numero)
fluid acceso feels king;          // inferito: binary
fluid amici feels ["Sara"];       // inferito: group
fluid nonbinary saluto feels "ciao";   // tipo esplicito: ancora valido
```

Una volta nata, la variabile **resta del suo tipo** (dichiarato o inferito): la
fluidità è libertà entro ciò che si è, non assenza di identità.

```js
fluid a feels 10;     // a è nonbinary
a feels 20;           // ok (ancora un numero)
a feels king;         // ERRORE: a è nonbinary, king è binary
```

Una variabile dichiarata **senza valore** assume un default secondo il tipo:
`binary` → `bi`, `group` → `[]`, `nonbinary` → `nil`.

> **Il `;` è opzionale.** Puoi chiudere le istruzioni con `;` oppure semplicemente
> andare a capo. Nel manifesto a volte lo scriviamo, a volte no: entrambe le forme
> sono valide.

---

## 3. Assegnare: `feels`

Il valore non viene "settato" né "uguagliato": viene **sentito**.

```
<nome> feels <valore>;
```

```js
fluid nonbinary umore feels "sereno";
umore feels "entusiasta";        // cambia, restando testo
umore feels 7;                   // ammesso: nonbinary accetta anche numeri

fluid binary luce feels queen;
luce feels king;                 // ok
luce feels bi;                   // ok: indefinito
luce feels "accesa";             // ERRORE: un binary sente solo king/queen/bi
```

`feels` rispetta sempre il tipo dichiarato con `fluid`. Puoi cambiare il valore
quante volte vuoi, ma non puoi tradire ciò che la variabile **è**.

---

## 4. Gli operatori parlano

In InclusiveScript i confronti e la logica non si scrivono con i simboli, ma con
**parole**. Si leggono come una frase.

| Operatore    | Significato            | Esempio                  |
|--------------|------------------------|--------------------------|
| `likes`      | uguale a               | `a likes b`              |
| `unlikes`    | diverso da             | `a unlikes b`            |
| `under`      | minore di              | `a under b`              |
| `underlikes` | minore o uguale a      | `a underlikes b`         |
| `over`       | maggiore di            | `a over b`               |
| `overlikes`  | maggiore o uguale a    | `a overlikes b`          |
| `not`        | negazione (logica)     | `not pronto`             |
| `and`        | e (entrambe vere)      | `pronto and attivo`      |
| `or`         | o (almeno una vera)    | `pronto or attivo`       |

L'idea è leggibile come una frase: `likes` / `unlikes` per l'uguaglianza, e i
confronti partono da `under` / `over`, a cui si aggiunge `likes` per includere
anche il caso "uguale" (`underlikes` = "minore o uguale").

```js
fluid nonbinary eta feels 18;

if (eta overlikes 18 and not (eta likes 99)) {
  print("maggiorenne");
}

print(3 unlikes 4);   // king   (3 e' diverso da 4)
print(5 under 2);     // queen
```

---

## 5. Le liste inclusive: il tipo `group`

In InclusiveScript non esistono array né tuple: c'è **una sola** struttura per
raccogliere valori, la **lista inclusiva**, del tipo `group`. Si dichiara con
`fluid group`, si scrive tra parentesi quadre e accoglie **qualsiasi** valore senza
distinzioni — testo, numeri, binary, perfino altre liste.

```js
fluid group numeri feels [10, 20, 30];
fluid group nomi feels ["Manuel", "Sara", "Luca"];
fluid group mista feels [1, "due", king, [4, 5]];
fluid group vuota;                  // senza valore -> lista vuota []
```

Si accede e si modifica un elemento con l'indice tra parentesi quadre (parte da 0):

```js
print(numeri[0]);      // 10
numeri[1] feels 25;    // modifica l'elemento in posizione 1
```

Per **aggiungere** e **togliere** elementi si usano due parole che dicono tutto:

```js
nomi inclusive "Ada";    // include un nuovo elemento (in fondo)
nomi exclusive "Sara";   // esclude la prima occorrenza del valore
```

È "inclusiva" anche perché non ti tradisce mai:

- **Accesso sicuro** — un indice fuori dai limiti restituisce `nil`, non un errore.
  ```js
  print(numeri[99]);   // nil  (niente crash)
  ```
- **Indici negativi** — `-1` è l'ultimo, `-2` il penultimo, e così via.
  ```js
  print(numeri[-1]);   // 30
  ```
- **Crescita dinamica** — assegnare oltre la fine allunga la lista, riempiendo con `nil`.
  ```js
  numeri[5] feels 99;  // [10, 25, 30, nil, nil, 99]
  ```

E porta con sé due funzioni native di supporto:

| Funzione                 | Cosa fa                                            |
|--------------------------|----------------------------------------------------|
| `len(lista)`             | quanti elementi contiene                           |
| `contains(lista, valore)`| dice se il valore è presente (`king`/`queen`)      |

---

## 6. Ciclare: `cycle`

Per ripetere si usa `cycle`. Lega sempre **due** nomi — l'elemento e la sua
posizione — e il corpo va racchiuso tra i **cuori**: `❤️` apre e `💔` chiude
(sono le parentesi graffe del linguaggio, e funzionano anche altrove).

**Su una lista** — `item` è l'elemento, `index` la posizione:

```js
fluid group nomi feels ["Manuel", "Sara", "Luca"];

cycle(persona, posizione in nomi) ❤️
  print(str(posizione) + ": " + persona);
💔
```

**Su un numero** — ripete N volte (`item` e `index` vanno entrambi da 0 a N-1):

```js
cycle(n, idx in 3) ❤️
  print("giro " + str(n));   // giro 0, giro 1, giro 2
💔
```

> I cuori sono intercambiabili con `{` e `}`. `cycle(...) ❤️ ... 💔` e
> `cycle(...) { ... }` sono la stessa cosa: scegli tu.

---

## 7. Decidere: l'`if` implicito

Per scegliere non serve dire `if`: basta una **condizione seguita da un cuore**.
Se la condizione è vera (`king`), si esegue il blocco.

```js
a likes 10 ❤️
  a feels 15
  b feels 22
💔
```

Si può aggiungere `else`, anche in catena (else-if):

```js
voto overlikes 9 ❤️
  print("ottimo")
💔 else voto overlikes 6 ❤️
  print("sufficiente")
💔 else ❤️
  print("insufficiente")
💔
```

Resta valida anche la forma classica con la parola `if` e le parentesi:
`if (a likes 10) { ... }`.

> La regola di lettura è semplice: un `;` chiude l'istruzione; senza `;`, un blocco
> che segue trasforma l'espressione precedente nella condizione di un `if`.

---

## 8. Le funzioni (e `be`)

Una funzione si definisce con `fun`, e **una funzione è una variabile** come le
altre: è un valore `nonbinary`, quindi può essere assegnata, passata, restituita.

```js
fun saluta(persona) ❤️
  return "Ciao " + persona
💔

fluid f feels saluta        // una funzione è un valore: la metto in una variabile
```

Per **invocarla** ci sono due modi equivalenti:

```js
print(saluta("Manuel"))     // forma classica, con le parentesi
be print saluta("Manuel")   // forma con 'be', senza parentesi attorno alla chiamata
```

Con `be` invochi una funzione **senza parentesi**: prima il nome, poi il primo
argomento separato da uno spazio; gli eventuali argomenti successivi vanno separati
da virgola.

```js
be print ""              // print con un argomento (riga vuota)
be print "ciao"
be saluta "Manuel"       // chiama saluta (il valore restituito viene ignorato)
be somma 3, 4            // due argomenti: somma(3, 4)
```

`print` è una funzione **di sistema**, già riconosciuta: scrive sulla console (come
il `print` di Python). Altre funzioni native: `clock`, `str`, `len`, `contains`.

> `be f arg` produce esattamente la stessa cosa di `f(arg)`: è solo un modo più
> diretto e leggibile per invocare. La forma con le parentesi resta sempre valida ed
> è quella da usare quando la chiamata è dentro un'espressione (es. `1 + f(x)`).

---

## 9. Le regole, in sintesi

| Concetto        | Sintassi                          | Regola                                              |
|-----------------|-----------------------------------|-----------------------------------------------------|
| Tipo `binary`   | `fluid binary x feels king;`      | `king` (sì) / `queen` (no) / `bi` (indefinito).     |
| Tipo `nonbinary`| `fluid nonbinary y feels "ok";`   | Testo, numeri, funzioni (non binary, non liste).    |
| Tipo `group`    | `fluid group g feels [a, b];`     | Una lista inclusiva (l'unica struttura dati).       |
| Dichiarazione   | `fluid [tipo] <nome> [feels v]`   | Tipo opzionale (se assente, inferito da `v`). `;` opzionale.|
| Assegnazione    | `<nome> feels <valore>`           | Cambia il valore, **rispettando il tipo**.          |
| Lista: aggiungi | `g inclusive <valore>`            | Include un elemento in fondo.                       |
| Lista: togli    | `g exclusive <valore>`            | Esclude la prima occorrenza del valore.             |
| Ciclo           | `cycle(item, index in X) ❤️ … 💔` | `X` è una lista o un numero (ripetizioni).          |
| Condizione      | `<cond> ❤️ … 💔 [else …]`         | `if` implicito; o classico `if (<cond>) { … }`.     |
| Funzione        | `fun nome(p) ❤️ … 💔`             | È un valore `nonbinary`.                            |
| Invocazione     | `be nome arg, arg` · `nome(arg)`  | Con o senza parentesi.                              |

---

## 10. Cosa è già vivo, oltre ai tipi

Queste regole convivono con il resto del linguaggio già implementato:

- funzioni con `fun`, `return`, ricorsione e **closure**; invocazione con `be` o `()` (sezione 8);
- controllo di flusso: `if` implicito (o esplicito) con `else`, `while`, `cycle`;
- liste inclusive (`group`) con accesso sicuro, indici negativi e crescita dinamica;
- operatori aritmetici (`+ - * /`, `+` concatena anche il testo);
- operatori di confronto e logici **a parole** (sezione 4);
  i valori binary `king`/`queen`/`bi` funzionano nelle condizioni e con gli operatori logici;
- funzioni native: `print`, `clock`, `str`, `len`, `contains`;
- commenti con `//`.

```js
fluid nonbinary nome feels "Manuel";
fluid binary saluta_forte feels king;

fun saluto(persona) {
  return "Ciao " + persona + "!";
}

if (saluta_forte) {
  print(saluto(nome));
}
```

---

## 11. Domande ancora aperte (decisioni di design future)

Il linguaggio è giovane. Alcuni punti sono volutamente lasciati in sospeso, da
decidere insieme:

- **`cycle` su un solo nome**: oggi servono sempre `item` e `index`. Vogliamo
  permettere anche `cycle(item in lista)` quando l'indice non serve?
- **Altri poteri delle liste**: ordinamento, slicing, `map`/`filter`, concatenazione.
- **Conversioni** tra tipi (es. da numero a testo) e operatori dedicati.
- **Distinzione testo/numero dentro `nonbinary`**: oggi un `nonbinary` può passare da
  testo a numero liberamente. È la scelta più "fluida", ma potremmo volerla irrigidire.
- Eventuali **parole chiave aggiuntive** coerenti con il tema.

> Questo manifesto descrive InclusiveScript così com'è oggi. È un documento vivo:
> cambierà insieme al linguaggio.
