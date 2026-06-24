"""
SimPL interactive shell.

Commands
────────
  load "file.sim"   — load definitions from a file
  clear             — reset the interpreter state
  types             — list all current definitions with their types
  exit / quit       — leave the shell
  <expr>            — evaluate an expression
  <name> = <expr>   — define a new name
"""
import sys
import os
from typing import Optional

from .lexer import LexError
from .parser import parse, parse_shell_input, ParseError
from .evaluator import Interpreter, SimPLError, Closure, BuiltinFunc
from .type_checker import (
    TypeEnv, infer, check_program, FuncType,
    NUM, BOOL, ANY, NONE,
)
from .ast_nodes import Definition, Node


# ── formatting helpers ────────────────────────────────────────────────────────

def _fmt_value(val) -> str:
    if isinstance(val, bool):
        return 'true' if val else 'false'
    if isinstance(val, float):
        # Suppress trailing zeros, but keep decimal point for reals
        s = f"{val:.10g}"
        return s
    if isinstance(val, Closure):
        return repr(val)
    if isinstance(val, BuiltinFunc):
        return repr(val)
    return str(val)


def _fmt_type(t) -> str:
    if isinstance(t, FuncType):
        return repr(t)
    return str(t)


# ── shell ─────────────────────────────────────────────────────────────────────

class Shell:
    BANNER = (
        "SimPL Interpreter v1.0\n"
        "  load \"file.sim\"  — load a file\n"
        "  clear            — reset environment\n"
        "  types            — show current definitions\n"
        "  exit / quit      — leave\n"
    )

    def __init__(self):
        self._reset()

    def _reset(self):
        self.interpreter = Interpreter()
        self.type_env    = TypeEnv()
        # Register built-in types
        from .type_checker import NUM, ANY
        for name, val in self.interpreter.global_env.bindings.items():
            if isinstance(val, BuiltinFunc):
                self.type_env.define(name, ANY)  # simplified: builtins are ANY

    # -- file loading --------------------------------------------------------

    def load(self, filename: str):
        path = filename.strip().strip('"').strip("'")
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {path!r}")
            return
        except OSError as e:
            print(f"Error reading file: {e}")
            return

        try:
            program = parse(source)
        except (LexError, ParseError) as e:
            print(f"Parse error: {e}")
            return

        try:
            self.interpreter.eval_program(program)
            types = check_program(program, self.type_env)
            count = len(program.defs)
            print(f"Loaded {count} definition(s) from '{os.path.basename(path)}'")
            for defn in program.defs:
                t = types.get(defn.name, ANY)
                print(f"  {defn.name} : {_fmt_type(t)}")
        except SimPLError as e:
            print(f"Runtime error: {e}")

    # -- single-line shell input ---------------------------------------------

    def process(self, line: str):
        line = line.strip()
        if not line:
            return

        # Shell meta-commands
        lower = line.lower()
        if lower in ('exit', 'quit', ':q'):
            sys.exit(0)

        if lower == 'clear':
            self._reset()
            print("Environment cleared.")
            return

        if lower == 'types':
            env = self.interpreter.global_env
            te  = self.type_env
            user_defs = {
                k: v for k, v in env.bindings.items()
                if not isinstance(v, BuiltinFunc)
            }
            if not user_defs:
                print("(no user definitions)")
            for name, val in user_defs.items():
                t = te.lookup(name)
                print(f"  {name} : {_fmt_type(t)} = {_fmt_value(val)}")
            return

        if line.startswith('load '):
            self.load(line[5:])
            return

        # Parse and evaluate
        try:
            node = parse_shell_input(line)
        except (LexError, ParseError) as e:
            print(f"Parse error: {e}")
            return

        try:
            if isinstance(node, Definition):
                val = self.interpreter.eval_definition(node)
                t   = infer(node.expr, self.type_env)
                self.type_env.define(node.name, t)
                print(f"{node.name} : {_fmt_type(t)} = {_fmt_value(val)}")
            else:
                val = self.interpreter.eval(node, self.interpreter.global_env)
                t   = infer(node, self.type_env)
                print(f"{_fmt_value(val)} : {_fmt_type(t)}")
        except SimPLError as e:
            print(f"Runtime error: {e}")
        except RecursionError:
            print("Runtime error: maximum recursion depth exceeded")

    # -- REPL loop -----------------------------------------------------------

    def run(self):
        print(self.BANNER)
        while True:
            try:
                line = input("> ")
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue
            self.process(line)
