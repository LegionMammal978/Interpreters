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
# but WITHval ANY WARRANTY; withval even the implied warranty of
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

# Divzeros interpreter by LegionMammal978
# see https://esolangs.org/wiki/Divzeros
# requires the lark-parser package from PyPI

def run(code):
    parser = Lark(r'''
        prog  : fndef* aexp
        fndef : NAME "=" aexp ";"
        ?aexp : [aexp "~"] bexp
        ?bexp : [bexp "$"] cexp
        ?cexp : [cexp "|"] dexp
        ?dexp : [dexp "^"] eexp
        ?eexp : [eexp "&"] fexp
        ?fexp : [fexp FOP] gexp
        FOP   : "+" | "-"
        ?gexp : [gexp GOP] hexp
        GOP   : "*" | "/" | "%"
        ?hexp : iexp | HOP hexp
        HOP   : "?" | "#" | "<" | ">" | "_" | "!"
        ?iexp : lit
              | "(" aexp ")"
              | IOP                 -> iop
              | "[" aexp "]"        -> sprog
              | NAME "(" aexp? ")"  -> fnap
              | NAME "(" STRING ")" -> fnsap
        IOP   : "?" | "#" | "@"
        NAME  : /[A-Za-z.,][A-Za-z.,0-9]*/
        lit   : INT | CHAR
        CHAR  : /'./s

        %import common.ESCAPED_STRING -> STRING
        %import common.INT
        %import common.WS
        %ignore WS
        %ignore /{{.*?}}/s
    ''', start='prog')
    class Evaluator(Interpreter):
        def prog(self, tree):
            self.fns = {}
            for fndef in tree.children[:-1]:
                self.visit(fndef)
            self.argstack = []
            self.iterstack = [[]]
            while True:
                try:
                    self.iterstack[0].append(self.visit(tree.children[-1]))
                except ZeroDivisionError:
                    break
        def fndef(self, tree):
            name = tree.children[0].value
            if name in self.fns:
                raise ValueError('cannot redefine function {}'.format(name))
            self.fns[name] = tree.children[1]
        def aexp(self, tree):
            arg1 = self.visit(tree.children[0])
            if arg1 == 0:
                return 0
            arg2 = self.visit(tree.children[1])
            bin1 = bin(arg1 if arg1 >= 0 else ~arg1)[2:]
            bin2 = bin(arg2 if arg2 >= 0 else ~arg2)[2:]
            sz = max(len(bin1), len(bin2))
            bin1 = bin1.zfill(sz)
            bin2 = bin2.zfill(sz)
            if arg1 >= 0 and arg2 >= 0:
                val = [i if j == '1' else '' for i, j in zip(bin1, bin2)]
                return int(''.join(val), 2) if len(val) > 0 else 0
            if arg1 < 0 and arg2 >= 0:
                bnot = {'0': '1', '1': '0'}
                val = [bnot[i] if j == '1' else '' for i, j in zip(bin1, bin2)]
                return int(''.join(val), 2) if len(val) > 0 else 0
            if arg1 >= 0 and arg2 < 0:
                val = [i if j == '0' else '' for i, j in zip(bin1, bin2)]
                return int(''.join(val), 2) if len(val) > 0 else 0
            if arg1 < 0 and arg2 < 0:
                val = [i if j == '0' else '' for i, j in zip(bin1, bin2)]
                return ~int(''.join(val), 2) if len(val) > 0 else -1
        def bexp(self, tree):
            arg1 = self.visit(tree.children[0])
            arg2 = self.visit(tree.children[1])
            if arg1*arg2 < 0:
                arg2 = ~arg2
            bin1 = bin(arg1 if arg1 >= 0 else ~arg1)[2:]
            bin2 = bin(arg2 if arg2 >= 0 else ~arg2)[2:]
            sz = max(len(bin1), len(bin2))
            bin1 = bin1.zfill(sz)
            bin2 = bin2.zfill(sz)
            val = int(''.join(i + j for i, j in zip(bin1, bin2)), 2)
            return val if arg1 >= 0 else ~val
        def cexp(self, tree):
            arg1 = self.visit(tree.children[0])
            if arg1 == -1:
                return -1
            arg2 = self.visit(tree.children[1])
            return arg1 | arg2
        def dexp(self, tree):
            arg1 = self.visit(tree.children[0])
            arg2 = self.visit(tree.children[1])
            return arg1 ^ arg2
        def eexp(self, tree):
            arg1 = self.visit(tree.children[0])
            if arg1 == 0:
                return 0
            arg2 = self.visit(tree.children[1])
            return arg1 & arg2
        def fexp(self, tree):
            arg1 = self.visit(tree.children[0])
            op = tree.children[1].value
            arg2 = self.visit(tree.children[2])
            if op == '+':
                return arg1 + arg2
            if op == '-':
                return arg1 - arg2
        def gexp(self, tree):
            arg1 = self.visit(tree.children[0])
            if arg1 == 0:
                return 0
            op = tree.children[1].value
            arg2 = self.visit(tree.children[2])
            if op == '*':
                return arg1*arg2
            if op == '/':
                return arg1//arg2
            if op == '%':
                return arg1 % arg2
        def hexp(self, tree):
            op = tree.children[0].value
            arg = self.visit(tree.children[1])
            if op == '?':
                sys.stdout.write(chr(arg))
                sys.stdout.flush()
                return arg
            if op == '#':
                arg -= 1
                if arg < 0:
                    if len(self.iterstack) < 2:
                        raise ValueError('main program has no parent')
                    if len(self.iterstack[-2]) == 0:
                        raise ValueError('parent program has no return value')
                    return self.iterstack[-2][-1]
                if arg >= len(self.iterstack[-1]):
                    raise ZeroDivisionError()
                return self.iterstack[-1][arg]
            if op in ('<', '>'):
                bina = bin(arg if arg >= 0 else ~arg)[2:]
                if len(bina) % 2 != 0:
                    bina = '0' + bina
                val = int(bina[::2] if op == '<' else bina[1::2], 2)
                return val if arg >= 0 else ~val
            if op == '_':
                return -arg
            if op == '!':
                return ~arg
        def iop(self, tree):
            op = tree.children[0].value
            if op == '?':
                val = sys.stdin.read(1)
                return ord(val) if val != '' else -1
            if op == '#':
                return len(self.iterstack[-1])
            if op == '@':
                if len(self.argstack) == 0:
                    raise ValueError('cannot read parameter outside function')
                if self.argstack[-1] is None:
                    raise ValueError('cannot read nonexistent parameter')
                return self.argstack[-1]
        def sprog(self, tree):
            self.iterstack.append([])
            while True:
                try:
                    self.iterstack[-1].insert(0, self.visit(tree.children[0]))
                except ZeroDivisionError:
                    break
            if len(self.iterstack[-1]) == 0:
                raise ValueError('subprogram has no return value')
            return self.iterstack.pop()[0]
        def fnap(self, tree):
            name = tree.children[0].value
            if name not in self.fns:
                raise ValueError('function {} not found'.format(name))
            if len(tree.children) > 1:
                arg = self.visit(tree.children[1])
            else:
                arg = None
            self.argstack.append(arg)
            val = self.visit(self.fns[name])
            self.argstack.pop()
            return val
        def fnsap(self, tree):
            name = tree.children[0].value
            if name not in self.fns:
                raise ValueError('function {} not found'.format(name))
            arg = tree.children[1].value[1:-1]
            arg = re.sub(r'\\(.)', r'\1', arg.replace(r'\n', '\n'))
            val = 0
            self.argstack.append(0)
            for c in arg:
                self.argstack[-1] = ord(c)
                val += self.visit(self.fns[name])
            self.argstack.pop()
            return val
        def lit(self, tree):
            ltype = tree.children[0].type
            if ltype == 'INT':
                return int(tree.children[0].value)
            if ltype == 'CHAR':
                return ord(tree.children[0].value[1])
    Evaluator().visit(parser.parse(code))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: {} file'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    try:
        run(code)
    except Exception as e:
        print('error: {}'.format(e), file=sys.stderr)
        sys.exit(1)
