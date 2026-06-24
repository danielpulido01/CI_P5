# SimPL Interpreter - implementado

## Estructura de archivos:
```text
simpl/
  __init__.py
  ast_nodes.py      — nodos del AST
  lexer.py          — tokenizador
  parser.py         — parser recursivo descendente
  type_checker.py   — inferencia de tipos (num/bool/any/none)
  evaluator.py      — intérprete de árbol
  shell.py          — REPL interactivo
simpl.py            — punto de entrada
gramatica_simpl.md  — gramática EBNF (20%)
examples/
  demo.sim          — demo completo del lenguaje
  sqrt_newton.sim   — método de Newton
  corridas.md       — corridas de ejemplo (10%)
```

## Para ejecutar:
```text
python simpl.py                    # shell interactivo
python simpl.py examples/demo.sim  # carga archivo y abre shell
```

## Características implementadas
- Lexer completo con comentarios `#`, int/real/bool, todas las palabras reservadas
- Parser para `lambda`/`fun`, `let...in`, `if...then...else`, llamadas a función, operadores aritméticos/booleanos/comparación
- **Ámbito léxico** con recursión mutua en el mismo nivel (placeholder pass)
- **Inferencia de tipos** con fixpoint: `num`, `bool`, `any`, `none(error)` — incluyendo tipos de función como `(num,num)->num`
- Shell con `load`, `clear`, `types`, evaluación de expresiones y definiciones
- Builtins: `abs`, `sqrt`, `floor`, `ceil`, `round`
- Detección de errores: duplicados, tipos incorrectos, errores de parseo