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

import re
import sys

from lark import Lark, LarkError, Transformer

# Complode interpreter by LegionMammal978
# see https://esolangs.org/wiki/Complode
# requires the lark-parser package from PyPI

def run(code):
    parser = Lark(r'''
        prog  : WS* ((cmd | macro) WS+)* (cmd | macro) WS*
        code  : WS+ (cmd WS+)*
        macro : "." CNAME "(" code ")"
        cmd   : SIGNED_INT   -> num
              | "/"          -> calc
              | "(" code ")" -> block
              | "," CNAME    -> ref
              | "_I"         -> inp
              | "_O"         -> outp

        %import common.CNAME
        %import common.SIGNED_INT
        %import common.WS
        %ignore ";" /[^\n]/*
    ''', start='prog')
    class Parser(Transformer):
        def __init__(self):
            self.macros = {}
            super().__init__()
        def SIGNED_INT(self, tok):
            return int(tok)
        def WS(self, tok):
            return None
        def __default__(self, data, args, meta):
            return [data, *args]
        def macro(self, args):
            if args[0] in self.macros:
                raise ValueError('duplicate macro {}'.format(args[0]))
            self.macros[args[0]] = args[1]
            return None
        def ref(self, args):
            if args[0] not in self.macros:
                raise ValueError('undefined macro {}'.format(args[0]))
            return ['ref', *args]
        def code(self, args):
            return [cmd for cmd in args if cmd is not None]
        def prog(self, args):
            return self.macros, [cmd for cmd in args if cmd is not None]
    def pop(allow_block=False):
        if len(stack) == 0:
            return 0
        if allow_block or isinstance(stack[-1], int):
            return stack.pop()
        block = stack.pop()
        while True:
            while len(stack) > 0 and stack.pop() != 0:
                eval_cmds(block)
            if len(stack) == 0:
                return 0
            if isinstance(stack[-1], int):
                return stack.pop()
            block = stack.pop()
    def calculation():
        a = pop()
        b = pop()
        c = pop()
        e = pop()
        f = pop()
        z = pop()
        if a > 0:
            if a not in var:
                var[a] = 0
            g = var[a]
        else:
            g = pop(True)
        if b > 0:
            if b not in var:
                var[b] = 0
            h = var[b]
        else:
            h = g
        if c > 0:
            var[c] = e
        if b > 0:
            var[b] = g if isinstance(g, list) else f*g
        if z > 0:
            stack.append(h if isinstance(h, list) else e + f + h)
        if z < 0 and a < 0 and b < 0:
            x = min(-a, -b)
            y = max(-a, -b)
            for n in range(x, y + 1):
                if n not in var:
                    var[n] = 0
            stash.append({n: val for n, val in var.items() if x <= n <= y})
        if z < 0 and a == 0 and b == 0 and len(stash) > 0:
            var.update(stash.pop())
        if z == 0 and a < 0:
            stack.append(e*f)
    def eval_cmds(cmds):
        ip = 0
        while ip < len(cmds):
            cmd = cmds[ip]
            if cmd[0] in ('num', 'block'):
                stack.append(cmd[1])
            elif cmd[0] == 'calc':
                calculation()
            elif cmd[0] == 'ref':
                eval_cmds(macros[cmd[1]])
            elif cmd[0] == 'inp':
                chin = sys.stdin.buffer.read(1)
                stack.append(chin[0] if chin else -1)
            elif cmd[0] == 'outp':
                sys.stdout.buffer.write(bytes([pop()]))
                sys.stdout.flush()
            ip += 1
    macros, cmds = Parser().transform(parser.parse(code))
    stack = []
    var = {}
    stash = []
    eval_cmds(cmds)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: {} file'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    try:
        run(code)
    except LarkError as e:
        print('parse error:\n{}'.format(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print('error: {}'.format(e), file=sys.stderr)
        sys.exit(1)
