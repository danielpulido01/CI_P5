# Tarea Programada - Especificación P5

## Especificación

En esta tarea su trabajo consiste en implementar un intérprete de un lenguaje mínimo desde principios a fin. Su intérprete debe tener un shell (command line) donde pueda cargar y ejecutar programas.

El lenguaje a implementar es **SimPL** (*Simple Programming Language*), y damos su especificación informal a continuación.

---

## El lenguaje SimPL

Primero listamos un programa válido en SimPL para que puedan hacerse una idea de cómo es el lenguaje:

```simpl
# JOSE CASTRO. Lenguajes de programación
# SIMPL language demo

x = 5;
f = fun(y) ~ x+y;

# Las siguientes dos funciones no requieren explicación

fact = lambda(n) ~
    if n = 0
        then 1
        else n*fact(n-1)
;

fib = lambda(n) ~
    if n < 3
        then 1
        else fib(n-1) + fib(n-2)
;

# definición de fib que ejecuta en tiempo lineal
# puntos extra si implementan recursión de cola
fib2 = lambda(n)
    let
        iter = fun(a,b,i) ~
            if i = n
                then b
                else iter(b,a+b,i+1)
    in
        iter(0,1,n);
```

```simpl
# Función para calcular el máximo común divisor,
# algoritmo de euclides
mcd = lambda(m,n) ~
    if m = n then m
    else if m > n then mcd(m-n,n)
    else mcd(n-m,m)
;

# Método de Newton para calcular pi  pi/2 = 1+1/2(1+2/3(1+3/5(1+ ...
pi = 2*pisum(1,20,3);

pisum = lambda(i,n,den) ~
    if i > n then 1
    else 1+(i/den)*pisum(i+1,n,den+2)

# Fórmula de Herón para calcular el area de un triángulo
areaTriangulo = lambda(a,b,c) ~ #
    let
        s = (a+b+c)/2
    in
        sqrt(s*(s-a)(s-b)(s-v));

# Método de Newton para calcular la raíz cuadrada
sqrt = lambda(n) ~
    let
        epsilon = 0.0000001;
        prox = lambda(x,n) ~ (x + n / x) / 2;
        sqrt = lambda(x,n) ~
            let
                val = prox(x,n)
            in
                if abs(val-n) < epsilon
                    then val
                    else sqrt(val,n);
```

---

## Características formales del lenguaje

Más formalmente, el lenguaje SimPL tiene las siguientes características:

1. Los identificadores tienen la estructura típica que se da en lenguajes como C.

2. Las palabras reservadas son:

   - `lambda`
   - `let`
   - `if`
   - `in`
   - `then`
   - `else`

3. Tiene tres tipos básicos:

   - `int`: ejemplos `-1`, `3`, `4`, `7`, etc.
   - `real`: ejemplos `0.534`, `123.432`. No se preocupe de parsear notación científica como `1.45E+8`.
   - `bool`: `true`, `false`.

4. Los operadores básicos de estos tipos son:

   ```text
   int    +, -, *, div, %    # el % corresponde al módulo o residuo
   real   +, -, *, /
   bool   &, |, !, ^         # el ^ corresponde al xor
   ```

5. Una declaración `lambda` tiene la forma:

   ```simpl
   lambda(<lista de variables>) ~ <expresión>
   ```

6. Una expresión `if` tiene la forma:

   ```simpl
   if <expresión bool>
       then <expresión then>  # ambas ramas deben ser del mismo tipo
       else <expresión else>
   ```

7. Una expresión `let` tiene la forma:

   ```simpl
   let
       a = <definición de a>;
       b = <definición de b>;
       ...
       z = <definición de z>
   in
       <expresión>
   ```

   Donde todos los valores definidos en el `let` son visibles en `<expresión>`.

8. Todo programa es una lista de definiciones de la forma:

   ```simpl
   a = <definición de a>;
   b = <definición de b>;
   ...
   z = <definición de z>
   ```

   Note que no hay punto y coma al final del programa. El punto y coma se usa **entre** definiciones nada más, el punto y coma es un separador, y no es parte de la `<definición>`, así que el parser solo debe aceptar el punto y coma después de una definición y antes de otra, no al final del archivo.

   Del lado izquierdo de las definiciones van identificadores, los cuales siguen las reglas estándar de un lenguaje como Java o C.

   Del lado derecho puede ir:

   - Una constante, como por ejemplo: `2`, `3.141592`, `true`, `false`, `-8`.
   - Una expresión aritmética o booleana con constantes y valores definidos en el mismo nivel.
   - La definición de una función `lambda`.
   - Una expresión `if`.
   - Una expresión `let`.

   Más adelante se especifican las tres construcciones básicas: `lambda`, `if` y `let`. Pero su semántica ya es conocida.

9. No se pueden repetir definiciones en el mismo nivel, pero sí se pueden generar en niveles distintos (*shadowing*).

   Es inválido:

   ```simpl
   a = <definición>;
   a = <otra definición>; # Error los identificadores son valores, no variables
   ```

   Pero sí es permitido:

   ```simpl
   a = <definición>;
   b = let a = <otra definición> in a; # válido
   ```

10. Es funcional puro, solo permite expresiones, y no hay comandos.

11. El ámbito de las definiciones es recursivo, esto es: definiciones de un mismo nivel se pueden ver entre sí.

   ```simpl
   a = b + 6; # ok b está al mismo nivel
   b = 5;
   c = sum(10);
   sum = lambda(n) if n=0 then 0 else n+sum(n-1)
   ```

12. Tiene binding dinámico (se resuelve en tiempo de ejecución).

13. Tiene ámbito estático o léxico (en tiempo de compilación).

14. Debe inferir el tipo de las funciones y de los parámetros de las funciones.

   Los tipos a inferir son:

   - `num`
   - `bool`
   - `any`
   - `none(error)`

   ### 14.1 Función de tipo `num`

   Una función de tipo `num` es una donde se puede garantizar que el valor de retorno es un número.

   Por ejemplo:

   ```simpl
   fact = lambda(n) ~
       if n = 0
           then 1
           else n*fact(n-1)
   ```

   Esta función es del tipo:

   ```text
   num -> num
   ```

   ### 14.2 Función de tipo `bool`

   Una función de tipo `bool` hace lo correspondiente pero para valores `bool`.

   ```simpl
   mayor = lambda(m,n) ~ m > n
   ```

   Esta función es de tipo:

   ```text
   (num, num) -> bool
   ```

   Esto porque la comparación solo se puede hacer sobre valores de tipo `num` y siempre devuelve un `bool`.

   Otra manera de verlo es que tiene el mismo tipo que la función `>`, el cual es:

   ```text
   > :: (num, num) -> bool
   ```

   ### 14.3 Función de tipo `any`

   Una función de tipo `any` es una que no se le puede definir el tipo, pero que no está mal construida y no tiene ningún conflicto de tipo evidente.

   ```simpl
   id = lambda(x) ~ x
   ```

   Esta función realmente es de tipo paramétrico:

   ```text
   a -> a
   ```

   Si la tratamos así, podemos instanciarla cuando alguien la llame. Por ejemplo:

   ```simpl
   id(5)     # num -> num
   id(true)  # bool -> bool
   ```

   Pero para efectos del proyecto se dejará como:

   ```text
   any -> any
   ```

   Se darán puntos extra si se agrega este tipo de inferencia de tipos.

   ### 14.4 Función de tipo `none`

   Una función de tipo `none` realmente es una función que tiene un conflicto de tipos y por lo tanto no pasa el análisis contextual.

   Por ejemplo:

   ```simpl
   nada = lambda(n,m) ~ (n > m) + 5
   ```

   `Nada` no tiene problemas en el análisis léxico, pero se queda pegada en el análisis contextual.

15. Los comentarios empiezan con `#` y se extienden hasta el fin de línea.

   ```simpl
   a = 5; # esto es un comentario #
   ```

---

## Nota de implementación

Debe internamente guardar los tipos de las funciones. Le conviene hacerlo, así podrá resolver tipos donde una función llama a otra, ya que en esos casos el tipo de la función llamada se necesita para discernir cuál es el tipo de la función principal.

---

## El shell

Su shell es simple. Debe implementar por lo menos:

```text
load “hola-mundo.sim”    # carga las definiciones de un texto.
clear                    # borra todas las definiciones de la memoria.
<expresión>              # puede ser cálculo numérico, booleano, o llamada a una función.
<nombre> = <expresión>   # definición de una variable
```

Una interacción con el shell puede ser:

```text
home> ./simpl
> load “prog.sim”
> pi
3.1415

> sqrt(9)
3.000001 # o algo así
```

---

## Entregables

- La gramática de SimPL. **20%**
- El compilador de SimPL. **60%**
- Su shell, puede ser el mismo programa que el punto anterior. **10%**
- Corridas ejemplo del programa SimPL. **10%**

---

## Fecha de entrega

No especificada en el documento.
