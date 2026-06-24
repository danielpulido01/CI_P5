from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple


@dataclass
class Node:
    pass


@dataclass
class IntLit(Node):
    value: int


@dataclass
class RealLit(Node):
    value: float


@dataclass
class BoolLit(Node):
    value: bool


@dataclass
class Ident(Node):
    name: str


@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node


@dataclass
class UnaryOp(Node):
    op: str
    operand: Node


@dataclass
class Lambda(Node):
    params: List[str]
    body: Node


@dataclass
class FuncCall(Node):
    func: Node
    args: List[Node]


@dataclass
class IfExpr(Node):
    cond: Node
    then_expr: Node
    else_expr: Node


@dataclass
class LetExpr(Node):
    defs: List[Tuple[str, Node]]
    body: Node


@dataclass
class Definition(Node):
    name: str
    expr: Node


@dataclass
class Program(Node):
    defs: List[Definition]
