"""
SimPL tree-walking interpreter.

Scoping rules
─────────────
• Lexical (static) scope: closures capture the *environment* at definition time.
• Recursive/mutually-recursive scope within the same level: all names in a
  block (program top-level or let-bindings) are inserted into the shared
  environment *before* evaluating any of their right-hand sides.  This lets
  definitions at the same level reference each other (including forward
  references and mutual recursion).
"""
import math
from typing import Any, Dict, List, Optional

from .ast_nodes import (
    Node, IntLit, RealLit, BoolLit, Ident, BinOp, UnaryOp,
    Lambda, FuncCall, IfExpr, LetExpr, Definition, Program,
)


# ── runtime error ─────────────────────────────────────────────────────────────

class SimPLError(Exception):
    pass


# ── environment ───────────────────────────────────────────────────────────────

class Environment:
    def __init__(self, parent: Optional['Environment'] = None):
        self.bindings: Dict[str, Any] = {}
        self.parent = parent

    def define(self, name: str, value: Any):
        self.bindings[name] = value

    def lookup(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        raise SimPLError(f"Undefined identifier: '{name}'")


# ── runtime values ────────────────────────────────────────────────────────────

class Closure:
    """User-defined function (lambda / fun)."""
    def __init__(self, params: List[str], body: Node, env: Environment):
        self.params = params
        self.body   = body
        self.env    = env  # captured (lexical) environment

    def __repr__(self):
        return f"<function({', '.join(self.params)})>"


class BuiltinFunc:
    def __init__(self, name: str, arity: int, fn):
        self.name  = name
        self.arity = arity
        self.fn    = fn

    def call(self, args: List[Any]) -> Any:
        if len(args) != self.arity:
            raise SimPLError(
                f"Built-in '{self.name}' expects {self.arity} argument(s), "
                f"got {len(args)}"
            )
        return self.fn(*args)

    def __repr__(self):
        return f"<builtin {self.name}>"


# ── interpreter ───────────────────────────────────────────────────────────────

class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self._register_builtins()

    # -- built-ins -----------------------------------------------------------

    def _register_builtins(self):
        builtins = [
            BuiltinFunc('abs',  1, lambda x: abs(x)),
            BuiltinFunc('sqrt', 1, lambda x: math.sqrt(x)),
            BuiltinFunc('floor',1, lambda x: int(math.floor(x))),
            BuiltinFunc('ceil', 1, lambda x: int(math.ceil(x))),
            BuiltinFunc('round',1, lambda x: round(float(x))),
        ]
        for b in builtins:
            self.global_env.define(b.name, b)

    # -- program / definition ------------------------------------------------

    def eval_program(self, program: Program):
        """Evaluate a full program, adding definitions to the global env."""
        # Check for duplicate names in this block
        names_seen = set()
        for defn in program.defs:
            if defn.name in names_seen:
                raise SimPLError(f"Duplicate definition: '{defn.name}'")
            if defn.name in self.global_env.bindings and defn.name not in self._builtins():
                raise SimPLError(f"Duplicate definition: '{defn.name}'")
            names_seen.add(defn.name)

        # First pass: register all names as None placeholders so that
        # closures created in this block can refer to siblings.
        for defn in program.defs:
            self.global_env.define(defn.name, None)

        # Second pass: evaluate and bind
        for defn in program.defs:
            val = self.eval(defn.expr, self.global_env)
            self.global_env.define(defn.name, val)

    def eval_definition(self, defn: Definition) -> Any:
        """Evaluate a single top-level definition from the shell."""
        if defn.name in self.global_env.bindings and defn.name not in self._builtins():
            raise SimPLError(f"Duplicate definition: '{defn.name}'")
        val = self.eval(defn.expr, self.global_env)
        self.global_env.define(defn.name, val)
        return val

    def _builtins(self):
        return {k for k, v in self.global_env.bindings.items()
                if isinstance(v, BuiltinFunc)}

    # -- expression dispatch -------------------------------------------------

    def eval(self, node: Node, env: Environment) -> Any:
        if isinstance(node, IntLit):
            return node.value
        if isinstance(node, RealLit):
            return node.value
        if isinstance(node, BoolLit):
            return node.value
        if isinstance(node, Ident):
            return env.lookup(node.name)
        if isinstance(node, BinOp):
            return self._eval_binop(node, env)
        if isinstance(node, UnaryOp):
            return self._eval_unary(node, env)
        if isinstance(node, Lambda):
            return Closure(node.params, node.body, env)
        if isinstance(node, FuncCall):
            return self._eval_call(node, env)
        if isinstance(node, IfExpr):
            return self._eval_if(node, env)
        if isinstance(node, LetExpr):
            return self._eval_let(node, env)
        raise SimPLError(f"Unknown AST node: {type(node).__name__}")

    # -- binary operators ----------------------------------------------------

    def _eval_binop(self, node: BinOp, env: Environment) -> Any:
        op = node.op
        left  = self.eval(node.left,  env)
        right = self.eval(node.right, env)

        # Arithmetic
        if op == '+':
            self._expect_num2(op, left, right)
            return self._arith(left + right, left, right)
        if op == '-':
            self._expect_num2(op, left, right)
            return self._arith(left - right, left, right)
        if op == '*':
            self._expect_num2(op, left, right)
            return self._arith(left * right, left, right)
        if op == '/':
            self._expect_num2(op, left, right)
            if right == 0:
                raise SimPLError("Division by zero")
            return float(left) / float(right)
        if op == 'div':
            if not (isinstance(left, int) and isinstance(right, int)):
                raise SimPLError("'div' requires integer operands")
            if right == 0:
                raise SimPLError("Division by zero")
            return left // right
        if op == '%':
            if not (isinstance(left, int) and isinstance(right, int)):
                raise SimPLError("'%' requires integer operands")
            if right == 0:
                raise SimPLError("Modulo by zero")
            return left % right

        # Comparisons
        if op == '=':
            return left == right
        if op == '<':
            return left < right
        if op == '>':
            return left > right
        if op == '<=':
            return left <= right
        if op == '>=':
            return left >= right
        if op == '!=':
            return left != right

        # Boolean logic
        if op == '&':
            self._expect_bool2(op, left, right)
            return left and right
        if op == '|':
            self._expect_bool2(op, left, right)
            return left or right
        if op == '^':
            self._expect_bool2(op, left, right)
            return bool(left) ^ bool(right)

        raise SimPLError(f"Unknown operator '{op}'")

    @staticmethod
    def _arith(result, left, right):
        """Promote to float if either operand is float."""
        if isinstance(left, float) or isinstance(right, float):
            return float(result)
        return result

    @staticmethod
    def _expect_num2(op, a, b):
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            raise SimPLError(f"Operator '{op}' requires numeric operands")

    @staticmethod
    def _expect_bool2(op, a, b):
        if not (isinstance(a, bool) and isinstance(b, bool)):
            raise SimPLError(f"Operator '{op}' requires boolean operands")

    # -- unary operators -----------------------------------------------------

    def _eval_unary(self, node: UnaryOp, env: Environment) -> Any:
        val = self.eval(node.operand, env)
        if node.op == '-':
            if not isinstance(val, (int, float)):
                raise SimPLError("Unary '-' requires a numeric operand")
            return -val
        if node.op == '!':
            if not isinstance(val, bool):
                raise SimPLError("'!' requires a boolean operand")
            return not val
        raise SimPLError(f"Unknown unary operator '{node.op}'")

    # -- function call -------------------------------------------------------

    def _eval_call(self, node: FuncCall, env: Environment) -> Any:
        func = self.eval(node.func, env)
        args = [self.eval(a, env) for a in node.args]

        if isinstance(func, BuiltinFunc):
            return func.call(args)

        if isinstance(func, Closure):
            if len(args) != len(func.params):
                raise SimPLError(
                    f"Function expects {len(func.params)} argument(s), "
                    f"got {len(args)}"
                )
            # New environment: lexical parent = closure's captured env
            call_env = Environment(func.env)
            for param, arg in zip(func.params, args):
                call_env.define(param, arg)
            return self.eval(func.body, call_env)

        raise SimPLError(f"'{func!r}' is not a function")

    # -- if ------------------------------------------------------------------

    def _eval_if(self, node: IfExpr, env: Environment) -> Any:
        cond = self.eval(node.cond, env)
        if not isinstance(cond, bool):
            raise SimPLError(
                f"'if' condition must be a boolean, got {_type_name(cond)}"
            )
        return self.eval(node.then_expr if cond else node.else_expr, env)

    # -- let -----------------------------------------------------------------

    def _eval_let(self, node: LetExpr, env: Environment) -> Any:
        let_env = Environment(env)
        # Placeholder pass for mutual recursion within let
        for name, _ in node.defs:
            let_env.define(name, None)
        for name, expr in node.defs:
            let_env.define(name, self.eval(expr, let_env))
        return self.eval(node.body, let_env)


def _type_name(val: Any) -> str:
    if isinstance(val, bool):
        return 'bool'
    if isinstance(val, int):
        return 'int'
    if isinstance(val, float):
        return 'real'
    if isinstance(val, Closure):
        return 'function'
    return type(val).__name__
