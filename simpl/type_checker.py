#SimPL type inference.

from typing import Dict, List, Optional, Tuple, Union
from .ast_nodes import (
    Node, IntLit, RealLit, BoolLit, Ident, BinOp, UnaryOp,
    Lambda, FuncCall, IfExpr, LetExpr, Definition, Program,
)

# type constants

NUM  = 'num'
BOOL = 'bool'
ANY  = 'any'
NONE = 'none'

Type = Union[str, 'FuncType']


class FuncType:
    def __init__(self, param_types: List[Type], return_type: Type):
        self.param_types = param_types
        self.return_type = return_type

    def __repr__(self):
        pts = ', '.join(_fmt(t) for t in self.param_types)
        if len(self.param_types) == 1:
            return f"{_fmt(self.param_types[0])} -> {_fmt(self.return_type)}"
        return f"({pts}) -> {_fmt(self.return_type)}"

    def __eq__(self, other):
        if not isinstance(other, FuncType):
            return False
        return self.param_types == other.param_types and self.return_type == other.return_type


def _fmt(t: Type) -> str:
    return repr(t) if isinstance(t, FuncType) else t


# type environment

class TypeEnv:
    def __init__(self, parent: Optional['TypeEnv'] = None):
        self.bindings: Dict[str, Type] = {}
        self.parent = parent

    def define(self, name: str, t: Type):
        self.bindings[name] = t

    def lookup(self, name: str) -> Type:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        return ANY  # unknown idents are treated as ANY

    def copy_into(self, other: 'TypeEnv'):
        for k, v in self.bindings.items():
            other.define(k, v)


# helpers

def _compatible(t1: Type, t2: Type) -> bool:
    if t1 == ANY or t2 == ANY:
        return True
    if isinstance(t1, FuncType) or isinstance(t2, FuncType):
        return False
    return t1 == t2


def _merge(t1: Type, t2: Type) -> Type:
    if t1 == t2:
        return t1
    if t1 == ANY:
        return t2
    if t2 == ANY:
        return t1
    return NONE  # conflict


# constraint collector for lambda params

def _constrain_param(name: str, node: Node, env: TypeEnv) -> Type:
    # Walk `node` to find what type `name` must have to make sense.
    # Returns the strongest type constraint found, or ANY.
    if isinstance(node, Ident):
        return ANY  # no constraint from identity alone

    if isinstance(node, BinOp):
        op = node.op
        uses_left  = _uses(name, node.left)
        uses_right = _uses(name, node.right)

        # Arithmetic operators always require NUM
        if op in ('+', '-', '*', '/', 'div', '%'):
            if uses_left or uses_right:
                return NUM

        # Boolean logic operators always require BOOL
        if op in ('&', '|', '^'):
            if uses_left or uses_right:
                return BOOL

        # Comparison operators ('<', '>', '<=', '>=') always compare numbers
        if op in ('<', '>', '<=', '>='):
            if uses_left or uses_right:
                return NUM  # these operators are numeric-only

        if op in ('=', '!='):
            # '=' and '!=' can compare bools or nums; infer from the other side,
            #  but fall back to NUM if the other side is also unknown.
            if uses_left:
                rt = infer(node.right, env)
                if rt == NUM:
                    return NUM
                if rt == BOOL:
                    return BOOL
                # Other side unknown — peek at right's own constraint
                rc = _constrain_param(name, node.right, env)
                if rc != ANY:
                    return rc
                return ANY
            if uses_right:
                lt = infer(node.left, env)
                if lt == NUM:
                    return NUM
                if lt == BOOL:
                    return BOOL
                lc = _constrain_param(name, node.left, env)
                if lc != ANY:
                    return lc
                return ANY

        # Recurse into sub-expressions to find deeper constraints
        t1 = _constrain_param(name, node.left, env)
        t2 = _constrain_param(name, node.right, env)
        return _merge(t1, t2)

    if isinstance(node, UnaryOp):
        if _uses(name, node.operand):
            return NUM if node.op == '-' else BOOL
        return _constrain_param(name, node.operand, env)

    if isinstance(node, IfExpr):
        tc = _constrain_param(name, node.cond, env)
        tt = _constrain_param(name, node.then_expr, env)
        te = _constrain_param(name, node.else_expr, env)
        return _merge(_merge(tc, tt), te)

    if isinstance(node, FuncCall):
        # If `name` appears as argument i of a call whose function type is
        # known, use the declared parameter type as the constraint.
        ft = infer(node.func, env)
        result = ANY
        for i, arg in enumerate(node.args):
            if _uses(name, arg):
                if isinstance(ft, FuncType) and i < len(ft.param_types):
                    # The function tells us what type this position must be
                    declared = ft.param_types[i]
                    result = _merge(result, declared)
                else:
                    # Function type unknown — recurse into the arg expression
                    at = _constrain_param(name, arg, env)
                    result = _merge(result, at)
        return result

    if isinstance(node, LetExpr):
        let_env = TypeEnv(env)
        for n, e in node.defs:
            let_env.define(n, infer(e, let_env))
        return _constrain_param(name, node.body, let_env)

    return ANY


def _uses(name: str, node: Node) -> bool:
    # Return True if `name` appears anywhere in `node`
    if isinstance(node, Ident):
        return node.name == name
    if isinstance(node, BinOp):
        return _uses(name, node.left) or _uses(name, node.right)
    if isinstance(node, UnaryOp):
        return _uses(name, node.operand)
    if isinstance(node, FuncCall):
        return _uses(name, node.func) or any(_uses(name, a) for a in node.args)
    if isinstance(node, IfExpr):
        return (_uses(name, node.cond) or
                _uses(name, node.then_expr) or
                _uses(name, node.else_expr))
    if isinstance(node, LetExpr):
        shadowed = any(n == name for n, _ in node.defs)
        defs_use = any(_uses(name, e) for _, e in node.defs)
        return defs_use or (not shadowed and _uses(name, node.body))
    if isinstance(node, Lambda):
        shadowed = name in node.params
        return not shadowed and _uses(name, node.body)
    return False


# main inference

def infer(node: Node, env: TypeEnv) -> Type:
    if isinstance(node, IntLit):
        return NUM
    if isinstance(node, RealLit):
        return NUM
    if isinstance(node, BoolLit):
        return BOOL
    if isinstance(node, Ident):
        return env.lookup(node.name)
    if isinstance(node, UnaryOp):
        t = infer(node.operand, env)
        if node.op == '-':
            return NUM if _compatible(t, NUM) else NONE
        if node.op == '!':
            return BOOL if _compatible(t, BOOL) else NONE
        return NONE
    if isinstance(node, BinOp):
        return _infer_binop(node, env)
    if isinstance(node, Lambda):
        return _infer_lambda(node, env)
    if isinstance(node, FuncCall):
        return _infer_call(node, env)
    if isinstance(node, IfExpr):
        cond_t = infer(node.cond, env)
        if cond_t not in (BOOL, ANY):
            return NONE
        then_t = infer(node.then_expr, env)
        else_t = infer(node.else_expr, env)
        return _merge(then_t, else_t)
    if isinstance(node, LetExpr):
        let_env = TypeEnv(env)
        for n, _ in node.defs:
            let_env.define(n, ANY)
        for n, e in node.defs:
            let_env.define(n, infer(e, let_env))
        return infer(node.body, let_env)
    return ANY


def _infer_binop(node: BinOp, env: TypeEnv) -> Type:
    op = node.op
    lt = infer(node.left, env)
    rt = infer(node.right, env)

    if op in ('+', '-', '*', '/', 'div', '%'):
        if _compatible(lt, NUM) and _compatible(rt, NUM):
            return NUM
        return NONE

    if op in ('=', '<', '>', '<=', '>=', '!='):
        if isinstance(lt, FuncType) or isinstance(rt, FuncType):
            return NONE
        if op == '=' and _compatible(lt, BOOL) and _compatible(rt, BOOL):
            return BOOL
        if _compatible(lt, NUM) and _compatible(rt, NUM):
            return BOOL
        if lt == ANY or rt == ANY:
            return BOOL
        return NONE

    if op in ('&', '|', '^'):
        if _compatible(lt, BOOL) and _compatible(rt, BOOL):
            return BOOL
        return NONE

    return ANY


def _infer_lambda(node: Lambda, env: TypeEnv) -> FuncType:
    # Pass 1: infer with params=ANY to let the environment stabilise
    func_env = TypeEnv(env)
    for p in node.params:
        func_env.define(p, ANY)
    infer(node.body, func_env)

    # Collect constraints for each parameter
    param_types: List[Type] = [
        _constrain_param(p, node.body, func_env) for p in node.params
    ]

    # Pass 2: re-infer body with constrained param types -> better return type
    func_env2 = TypeEnv(env)
    for p, pt in zip(node.params, param_types):
        func_env2.define(p, pt)
    ret_t = infer(node.body, func_env2)

    return FuncType(param_types, ret_t)


def _infer_call(node: FuncCall, env: TypeEnv) -> Type:
    ft = infer(node.func, env)
    if isinstance(ft, FuncType):
        return ft.return_type
    if ft == ANY:
        return ANY
    return NONE


# program-level check

def check_program(program: Program, env: Optional[TypeEnv] = None) -> Dict[str, Type]:
    if env is None:
        env = TypeEnv()
    # Seed all names as ANY for mutual recursion
    for defn in program.defs:
        env.define(defn.name, ANY)
    # Iterate to fixpoint (handles recursive/mutually-recursive definitions)
    changed = True
    while changed:
        changed = False
        for defn in program.defs:
            t = infer(defn.expr, env)
            old = env.lookup(defn.name)
            if t != old:
                env.define(defn.name, t)
                changed = True
    return {defn.name: env.lookup(defn.name) for defn in program.defs}