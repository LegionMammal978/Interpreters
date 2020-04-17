#!/usr/bin/env python3
#
# Copyright (C) 2020  LegionMammal978
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import math
import re
import sys

from lark import Lark, LarkError
from lark.visitors import Interpreter

# And interpreter by LegionMammal978
# see https://esolangs.org/wiki/And
# requires the lark-parser package from PyPI

# interpreter features:
#  - all characters are integers
#  - all strings are integer arrays
#  - all variables are initialized to 0
#  - arrays are expanded automatically
#  - boolean operators are &&, ||, and !
#  - relational operators are =, !=, <, >, <=, and >=
#  - value operators are +, -, *, /, and %
#  - print only prints chars and strings; use + "" to print values
#  - -n suppresses automatic newlines after print statements

def run(code, print_newline=True):
    parser = Lark(r'''
        ?eor  : eand ("||" eand)*
        ?eand : bool ("&&" bool)*
        ?bool : notp | test
        ?notp : NOT* "(" eor ")"
        NOT   : "!"
        test  : "exit"      -> eexit
              | "true"      -> true
              | "false"     -> false
              | "print" add -> eprint
              | add TOP add
        TOP   : "=" | "!=" | "<" | ">" | "<=" | ">=" | ":="
        ?add  : mult (AOP mult)*
        AOP   : "+" | "-"
        ?mult : neg (MOP neg)*
        MOP   : "*" | "/" | "%"
        ?neg  : NEG* prim
        NEG   : "-"
        ?prim : lit
              | "input"          -> einput
              | CNAME            -> id
              | "(" add ")"
              | prim "[" add "]" -> idx
        lit   : INT | CHAR | STRING
        CHAR  : /'([^\\']|\\.)'/

        %import common.CNAME
        %import common.ESCAPED_STRING -> STRING
        %import common.INT
        %import common.WS
        %ignore WS
    ''', start='eor')
    class Evaluator(Interpreter):
        def eor(self, tree):
            for child in tree.children:
                res = self.visit(child)
                if res:
                    return True
            return False
        def eand(self, tree):
            for child in tree.children:
                res = self.visit(child)
                if not res:
                    return False
            return True
        def notp(self, tree):
            res = self.visit(tree.children[-1])
            return res ^ (len(tree.children) % 2 == 0)
        def test(self, tree):
            op = tree.children[1].value
            if op == ':=':
                rhs = self.visit(tree.children[2])
                lhs = tree.children[0]
                idxs = []
                while lhs.data != 'id':
                    if lhs.data != 'idx':
                        raise ValueError('invalid assignment LHS')
                    idx = self.visit(lhs.children[1])
                    if not isinstance(idx, int):
                        raise ValueError('invalid index type')
                    if idx < 0:
                        raise ValueError('negative index')
                    idxs.insert(0, idx)
                    lhs = lhs.children[0]
                var = lhs.children[0].value
                if len(idxs) == 0:
                    vardict[var] = rhs
                    return True
                if var not in vardict:
                    vardict[var] = []
                var = vardict[var]
                for idx in idxs[:-1]:
                    if idx >= len(var):
                        var.extend([0] * (idx-len(var)+1))
                    if not isinstance(var[idx], list):
                        var[idx] = []
                    var = var[idx]
                if idxs[-1] >= len(var):
                    var.extend([0] * (idxs[-1]-len(var)+1))
                var[idxs[-1]] = rhs
                return True
            arg1 = self.visit(tree.children[0])
            arg2 = self.visit(tree.children[2])
            if op == '=':
                return arg1 == arg2
            if op == '!=':
                return arg1 != arg2
            if op == '<':
                return arg1 < arg2
            if op == '>':
                return arg1 > arg2
            if op == '<=':
                return arg1 <= arg2
            if op == '>=':
                return arg1 >= args
        def true(self, tree):
            return True
        def false(self, tree):
            return False
        def eexit(self, tree):
            sys.exit()
        def eprint(self, tree):
            arg = self.visit(tree.children[0])
            if isinstance(arg, int):
                arg = [arg]
            out = ''
            for ch in arg:
                try:
                    out += chr(ch)
                except ValueError:
                    raise ValueError('invalid character')
            print(out, end='\n' if print_newline else '', flush=True)
            return True
        def add(self, tree):
            val = self.visit(tree.children[0])
            for i in range(1, len(tree.children) - 1, 2):
                op = tree.children[i].value
                arg = self.visit(tree.children[i + 1])
                if op == '+':
                    if isinstance(val, int) and isinstance(arg, list):
                        val = [ord(ch) for ch in str(val)]
                    elif isinstance(val, list) and isinstance(arg, int):
                        arg = [ord(ch) for ch in str(arg)]
                    val = val + arg
                if op == '-':
                    if not isinstance(val, int) or not isinstance(arg, int):
                        raise ValueError('invalid operand')
                    val = val - arg
            return val
        def mult(self, tree):
            val = self.visit(tree.children[0])
            if not isinstance(val, int):
                raise ValueError('invalid operand')
            for i in range(1, len(tree.children) - 1, 2):
                op = tree.children[i].value
                arg = self.visit(tree.children[i + 1])
                if not isinstance(arg, int):
                    raise ValueError('invalid operand')
                if op == '*':
                    val = val * arg
                if op == '/':
                    val = val//arg if val*arg > 0 else -(-val//arg)
                if op == '%':
                    val = math.fmod(val, arg)
            return val
        def neg(self, tree):
            arg = self.visit(tree.children[-1])
            if len(tree.children) > 1 and not isinstance(arg, int):
                raise ValueError('invalid operand')
            if len(tree.children) % 2 == 0:
                arg *= -1
            return arg
        def einput(self, tree):
            if self.inchar is None:
                self.inchar = sys.stdin.read(1)
            if self.inchar == '':
                return -1
            return ord(self.inchar)
        def id(self, tree):
            var = tree.children[0].value
            if var not in vardict:
                vardict[var] = 0
            return vardict[var]
        def idx(self, tree):
            if tree.children[0].data == 'id':
                var = tree.children[0].children[0].value
                if var not in vardict:
                    vardict[var] = []
            arr = self.visit(tree.children[0])
            idx = self.visit(tree.children[1])
            if not isinstance(arr, list):
                raise ValueError('cannot index integer')
            if not isinstance(idx, int):
                raise ValueError('invalid index type')
            if idx < 0:
                raise ValueError('negative index')
            if idx >= len(arr):
                arr.extend([0] * (idx-len(arr)+1))
            return arr[idx]
        def lit(self, tree):
            ltype = tree.children[0].type
            if ltype == 'INT':
                return int(tree.children[0].value)
            if ltype == 'CHAR':
                val = tree.children[0].value[1:-1]
                if val == '\\n':
                    return 10
                elif val[0] == '\\':
                    return ord(val[1])
                else:
                    return ord(val)
            if ltype == 'STRING':
                val = tree.children[0].value[1:-1]
                val = re.sub(r'\\(.)', r'\1', val.replace(r'\n', '\n'))
                return [ord(ch) for ch in val]
    tree = parser.parse(code)
    vardict = {}
    ev = Evaluator()
    while True:
        ev.inchar = None
        ev.visit(tree)

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] == '-n' and len(sys.argv) < 3:
        print('usage: {} [-n] file'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(2)
    pr_nl = sys.argv[1] != '-n'
    with open(sys.argv[1 if pr_nl else 2], 'r') as f:
        code = f.read()
    try:
        run(code, pr_nl)
    except LarkError as e:
        print('parse error:\n{}'.format(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print('error: {}'.format(e), file=sys.stderr)
        sys.exit(1)
