# Gramática de SimPL

## Notación

La gramática usa la notación EBNF:

- `A ::= B C`         — A produce B seguido de C
- `A ::= B | C`       — A produce B o C (alternativa)
- `{A}`               — cero o más repeticiones de A
- `[A]`               — A es opcional (cero o una vez)
- Terminales entre comillas simples: `'lambda'`, `'('`, etc.
- No terminales en _itálica_ o en minúsculas: _expr_, _id_

---

## Gramática completa

```
program     ::= definition { ';' definition }

definition  ::= IDENT '=' expr

expr        ::= let_expr
              | if_expr
              | lambda_expr
              | bool_expr

let_expr    ::= 'let'
                    definition { ';' definition }
                'in'
                    expr

if_expr     ::= 'if' expr 'then' expr 'else' expr

lambda_expr ::= ( 'lambda' | 'fun' ) '(' params ')' ['~'] expr

params      ::= IDENT { ',' IDENT }
              | ε                          (* función sin parámetros *)

bool_expr   ::= cmp_expr { bool_op cmp_expr }
bool_op     ::= '&' | '|' | '^'

cmp_expr    ::= add_expr [ cmp_op add_expr ]
cmp_op      ::= '=' | '<' | '>' | '<=' | '>=' | '!='

add_expr    ::= mul_expr { add_op mul_expr }
add_op      ::= '+' | '-'

mul_expr    ::= unary_expr { mul_op unary_expr }
mul_op      ::= '*' | '/' | 'div' | '%'

unary_expr  ::= '!' unary_expr
              | '-' unary_expr
              | postfix_expr

postfix_expr ::= primary_expr { '(' args ')' }
args         ::= expr { ',' expr }
               | ε

primary_expr ::= INT_LIT
               | REAL_LIT
               | BOOL_LIT
               | IDENT
               | '(' expr ')'
```

---

## Tokens (expresiones regulares)

```
INT_LIT   ::= [0-9]+
REAL_LIT  ::= [0-9]+ '.' [0-9]+
BOOL_LIT  ::= 'true' | 'false'
IDENT     ::= [a-zA-Z_] [a-zA-Z0-9_]*
COMMENT   ::= '#' .* '\n'          (* se descarta *)
```

### Palabras reservadas (no válidas como IDENT)

`lambda`, `fun`, `let`, `in`, `if`, `then`, `else`, `div`, `true`, `false`

---

## Asociatividad y precedencia de operadores

De **mayor** a **menor** precedencia:

| Nivel | Operadores          | Asociatividad |
|-------|---------------------|---------------|
| 6     | `-x`, `!x` (unarios)| Derecha       |
| 5     | `*`, `/`, `div`, `%`| Izquierda     |
| 4     | `+`, `-`            | Izquierda     |
| 3     | `=`, `<`, `>`, `<=`, `>=`, `!=` | Izquierda |
| 2     | `&`, `\|`, `^`      | Izquierda     |
| 1     | `if … then … else …`| Derecha       |
| 1     | `let … in …`        | —             |
| 1     | `lambda(…) ~ …`     | —             |

---

## Semántica informal

| Construcción | Semántica |
|---|---|
| `let x = e1 in e2` | Evalúa `e1`, liga el resultado a `x` en el ámbito de `e2` |
| `if b then e1 else e2` | Evalúa `b`; si es `true` devuelve `e1`, si no `e2` |
| `lambda(x) ~ e` | Cierre léxico: captura el entorno en el momento de definición |
| `f(a, b)` | Aplica la función `f` a los argumentos |
| `div` | División entera (solo enteros) |
| `%` | Módulo / residuo (solo enteros) |
| `/` | División real (devuelve `real`) |

---

## Sistema de tipos inferidos

| Tipo   | Descripción |
|--------|-------------|
| `num`  | Número (entero o real) |
| `bool` | Valor booleano |
| `any`  | Tipo no resuelto / paramétrico |
| `none` | Conflicto de tipos (error estático) |

Los tipos de funciones se expresan como `T1 -> T2` o `(T1, T2) -> T3`.

Ejemplos:

```text
fact  :: num -> num
mayor :: (num, num) -> bool
id    :: any -> any
nada  :: (num, num) -> none    (* error de tipo *)
```

---

## Ejemplo de derivación

Programa: `a = 2 + 3 * 4`

```
program
  └─ definition
       ├─ IDENT  'a'
       └─ expr → bool_expr → cmp_expr → add_expr
                   ├─ mul_expr → unary_expr → postfix_expr → INT_LIT(2)
                   └─ '+' mul_expr
                             ├─ unary_expr → INT_LIT(3)
                             └─ '*' unary_expr → INT_LIT(4)
```

Resultado: `a = 14`
