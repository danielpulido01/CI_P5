# SimPL Interpreter
---

## Cómo ejecutar

```
python simpl.py                    # abre el shell interactivo
python simpl.py examples/demo.sim  # carga el archivo y abre el shell
```

---

# Corridas ejemplo — SimPL

## Corrida 1 — Shell básico

```
SimPL Interpreter v1.0

> x = 5
x : num = 5

> y = x * 2 + 1
y : num = 11

> y
11 : num

> x + y
16 : num

> true & !false
true : bool

> 10 div 3
3 : num

> 10 % 3
1 : num
```

---

## Corrida 2 — Carga de archivo y funciones

```
> load "examples/demo.sim"
Loaded 12 definition(s) from 'demo.sim'
  x : num
  pi : num
  flag : bool
  area : num
  double : num -> num
  fact : num -> num
  fib : num -> num
  fib2 : any -> num
  mcd : (num, num) -> num
  both : (bool, bool) -> bool
  either : (bool, bool) -> bool
  negate : bool -> bool

> fact(10)
3628800 : num

> fib(15)
610 : num

> fib2(30)
832040 : num

> mcd(100, 75)
25 : num

> mcd(48, 18)
6 : num

> area
78.5398 : num
```

---

## Corrida 3 — Expresiones let y shadowing

```
> let a = 3; b = 4 in a * a + b * b
25 : num

> a = 10
a : num = 10

> b = let a = 99 in a + 1
b : num = 100

> a
10 : num

> b
100 : num
```

---

## Corrida 4 — Tipos inferidos

```
> fact = lambda(n) ~ if n = 0 then 1 else n * fact(n-1)
fact : num -> num = <function(n)>

> mayor = lambda(m,n) ~ m > n
mayor : (num, num) -> bool = <function(m, n)>

> id = lambda(x) ~ x
id : any -> any = <function(x)>

> nada = lambda(n,m) ~ (n > m) + 5
nada : (num, num) -> none = <function(n, m)>
```

---

## Corrida 5 — Recursión mutua

```
> isEven = lambda(n) ~ if n = 0 then true  else isOdd(n-1)
isEven : num -> bool = <function(n)>

> isOdd  = lambda(n) ~ if n = 0 then false else isEven(n-1)
isOdd : num -> bool = <function(n)>

> isEven(10)
true : bool

> isOdd(7)
true : bool
```

---

## Corrida 6 — Funciones de orden superior con let

```
> compose = lambda(f,g) ~ lambda(x) ~ f(g(x))
compose : (any, any) -> any -> any = <function(f, g)>

> double = lambda(n) ~ n * 2
double : num -> num = <function(n)>

> inc = lambda(n) ~ n + 1
inc : num -> num = <function(n)>

> doubleThenInc = compose(inc, double)
doubleThenInc : any -> any = <function(x)>

> doubleThenInc(5)
11 : any
```

---

## Corrida 7 — Método de Newton (sqrt_newton.sim)

```
> load "examples/sqrt_newton.sim"
Loaded 4 definition(s) from 'sqrt_newton.sim'
  epsilon : num
  prox : (num, num) -> num
  sqrtIter : (num, num) -> num
  mySqrt : num -> num

> mySqrt(9)
3 : num

> mySqrt(2)
1.414213562 : num

> mySqrt(144)
12 : num
```

---

## Corrida 8 — Errores

```
> undeclared
Runtime error: Undefined identifier: 'undeclared'

> 1 + true
Runtime error: Operator '+' requires numeric operands

> fact(5
Parse error: Expected RPAREN, got EOF (None) at line 1

> a = 5; a = 6
Runtime error: Duplicate definition: 'a'
```
