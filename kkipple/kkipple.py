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

# Kkipple interpreter by LegionMammal978
# see https://esolangs.org/wiki/Kkipple

digs = '0123456789'
spat = '&@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'

def run(code):
    exec_pos = None
    exec_count = 0
    def rc(code, idx):
        if exec_pos is not None:
            return exec_pos
        return (code.count('\n', 0, idx) + 1, idx - code.rfind('\n', 0, idx))
    def pos_error(msg, code, idx, *args):
        return ValueError(('row {} col {}: ' + msg).format(*rc(code, idx),
                                                           *args))
    def parse(code):
        ops = []
        lstack = []
        last, last_pos = None, -1
        immed = False
        ip = 0
        while ip < len(code):
            c = code[ip]
            if ord(c) > 126:
                raise pos_error('invalid character {}', code, ip, repr(c))
            elif c.isspace():
                immed = False
                ip += 1
            elif c == '#':
                immed = False
                while ip < len(code) and code[ip] != '\n':
                    ip += 1
            elif c in '><+-':
                if last and last[0] in 'bl':
                    raise pos_error('missing right argument', code, last_pos)
                if not last or last[0] not in 'sna':
                    raise pos_error('missing left argument', code, ip)
                if c in '<+-' and last[0] != 's':
                    raise pos_error('invalid left argument', code, ip)
                immed = False
                last, last_pos = 'b' + c + last, ip
                ip += 1
            elif c in '?*':
                if last and last[0] in 'bl':
                    raise pos_error('missing right argument', code, last_pos)
                if immed and last and last[0] == 's':
                    ops.append(('u' + c, rc(code, ip), last))
                immed = True
                last, last_pos = 'u' + c, ip
                ip += 1
            elif c == '(':
                if last and last[0] in 'bl':
                    raise pos_error('missing right argument', code, last_pos)
                immed = False
                last, last_pos = 'l', ip
                ip += 1
            elif c == ')':
                if last and last[0] in 'bl':
                    raise pos_error('missing right argument', code, last_pos)
                if len(lstack) == 0:
                    raise pos_error('too many ) operators', code, ip)
                lops = ops
                pos, sid, ops = lstack.pop()
                ops.append(('l', pos, sid, lops))
                immed = False
                last, last_pos = None, ip
                ip += 1
            elif (c in spat or c == '0' and (ip + 1 == len(code)
                                             or code[ip + 1] not in digs)):
                sid = 's'
                pos = ip
                while ip < len(code) and (code[ip] in spat
                                          or ip == pos and code[ip] == '0'):
                    sid += code[ip]
                    ip += 1
                if sid == 'so':
                    sid = 'sio'
                if last and last[0] == 'b':
                    ops.append((last[:2], rc(code, last_pos), last[2:], sid))
                elif immed and last and last[0] == 'u':
                    ops.append((last, rc(code, last_pos), sid))
                elif last and last[0] == 'l':
                    lstack.append((rc(code, last_pos), sid, ops))
                    ops = []
                immed = True
                last, last_pos = sid, pos
            elif c in digs or c == "'":
                if last and (last[0] == 'l' or last[:2] == 'b>'):
                    raise pos_error('invalid right argument', code, last_pos)
                pos = ip
                if c == "'":
                    if (ip + 2 >= len(code)
                        or code[ip + 1] == '\\' and ip + 3 >= len(code)):
                        raise pos_error('unterminated char literal', code, pos)
                    ip += 1
                    if code[ip] == '\\':
                        ip += 1
                        if code[ip] == 'n':
                            val = 'n10'
                        else:
                            val = 'n' + str(ord(code[ip]))
                    else:
                        val = 'n' + str(ord(code[ip]))
                    if code[ip + 1] != "'":
                        raise pos_error('unterminated char literal', code, pos)
                    ip += 2
                else:
                    val = 'n'
                    while ip < len(code) and code[ip] in digs:
                        val += code[ip]
                        ip += 1
                if last and last[0] == 'b':
                    ops.append((last[:2], rc(code, last_pos), last[2:], val))
                immed = False
                last, last_pos = val, pos
            elif c == '"':
                if last and (last[0] == 'l' or last[:2] == 'b>'):
                    raise pos_error('invalid right argument', code, last_pos)
                val = 'a'
                pos = ip
                ip += 1
                while ip < len(code) and code[ip] != '"':
                    if code[ip] == '\\':
                        ip += 1
                        if ip == len(code):
                            raise pos_error('unterminated string literal',
                                            code, pos)
                        if code[ip] == 'n':
                            val += '\n'
                        else:
                            val += code[ip]
                    else:
                        val += code[ip]
                    ip += 1
                if ip == len(code):
                    raise pos_error('unterminated string literal', code, pos)
                ip += 1
                if last and last[0] == 'b':
                    ops.append((last[:2], rc(code, last_pos), last[2:], val))
                immed = False
                last, last_pos = val, pos
            else:
                raise pos_error('invalid character {}', code, ip, repr(c))
        if len(lstack) > 0:
            raise pos_error('missing ) operators', code, lstack[-1][1])
        return ops
    class Stack:
        def __init__(self):
            self.vals = []
        def is_empty(self):
            return len(self.vals) == 0
        def push(self, val):
            self.vals.append(val)
        def peek(self):
            if self.is_empty():
                return 0
            else:
                return self.vals[-1]
        def pop(self):
            top = self.peek()
            if not self.is_empty():
                self.vals.pop()
            return top
        def test(self):
            if self.peek() == 0:
                self.vals.clear()
        def trigger(self, pos):
            pass
    class IOStack(Stack):
        def getch(self):
            inc = sys.stdin.read(1)
            self.push(ord(inc) if inc else 0)
        def peek(self):
            if self.is_empty():
                self.getch()
            return super().peek()
        def trigger(self, pos):
            while not self.is_empty():
                val = self.pop()
                if not 0 <= val <= sys.maxunicode:
                    raise ValueError(
                        'invalid codepoint {} in I/O stack'.format(val)
                    )
                sys.stdout.write(chr(val))
            sys.stdout.flush()
    class DigitsStack(Stack):
        def __init__(self):
            self.ntd = True
            super().__init__()
        def push(self, val):
            if self.ntd:
                for c in str(val):
                    super().push(ord(c))
            else:
                super().push(val)
        def trigger(self, pos):
            if self.is_empty():
                self.ntd = not self.ntd
                return
            val = 0
            while not self.is_empty():
                d = self.pop()
                if not 48 <= d < 58:
                    raise ValueError(
                        'invalid digit {} in digits stack'.format(d)
                    )
                val = 10*val + int(chr(d))
            self.ntd = not self.ntd
            self.push(val)
    class ExecStack(Stack):
        def push(self, val):
            if exec_count > 0:
                raise ValueError('cannot modify execute stack within itself')
            super().push(val)
        def pop(self):
            if exec_count > 0:
                raise ValueError('cannot modify execute stack within itself')
            return super().pop()
        def test(self):
            if exec_count > 0:
                raise ValueError('cannot modify execute stack within itself')
            super().test()
        def trigger(self, pos):
            ecode = ''
            while not self.is_empty():
                val = self.pop()
                if not 0 <= val <= sys.maxunicode:
                    raise ValueError(
                        'invalid codepoint {} in execute stack'.format(val)
                    )
                ecode += chr(val)
            exec_pos = pos
            try:
                eops = parse(ecode)
            except ValueError as e:
                raise ValueError(str(e) + ' in execute stack')
            ops[:0] = eops
            exec_count += len(eops)
    class NullStack(Stack):
        def push(self, val):
            pass
    class CopyStack(Stack):
        def __init__(self):
            self.vals = [0]
        def push(self, val):
            self.vals = [val]
        def pop(self):
            return self.peek()
        def test(self):
            pass
    stacks = {
        'sio': IOStack(), 's@': DigitsStack(), 's&': ExecStack(),
        's0': NullStack(), 'sC': CopyStack()
    }
    def get_vs(arg, copy, rev=False):
        if arg[0] == 's':
            if copy:
                return [stacks[arg].peek()]
            return [stacks[arg].pop()]
        elif arg[0] == 'a':
            if rev:
                return [ord(c) for c in arg[:0:-1]]
            return [ord(c) for c in arg[1:]]
        return [int(arg[1:])]
    ops = parse(code)
    while len(ops) > 0:
        op, pos, *args = ops.pop(0)
        if op[0] in 'bul' and args[0][0] == 's' and args[0] not in stacks:
            stacks[args[0]] = Stack()
        if op[0] == 'b' and args[1][0] == 's' and args[1] not in stacks:
            stacks[args[1]] = Stack()
        try:
            if op == 'b>':
                s = stacks[args[1]]
                for v in get_vs(args[0], isinstance(s, CopyStack), True):
                    s.push(v)
            elif op == 'b<':
                s = stacks[args[0]]
                for v in get_vs(args[1], isinstance(s, CopyStack)):
                    s.push(v)
            elif op == 'b+':
                s = stacks[args[0]]
                for v in get_vs(args[1], isinstance(s, CopyStack)):
                    s.push(s.pop() + v)
            elif op == 'b-':
                s = stacks[args[0]]
                for v in get_vs(args[1], isinstance(s, CopyStack)):
                    s.push(s.pop() - v)
            elif op == 'u?':
                stacks[args[0]].test()
            elif op == 'u*':
                    stacks[args[0]].trigger(pos)
            elif op == 'l':
                if not stacks[args[0]].is_empty():
                    ops.insert(0, (op, pos, *args))
                    ops[:0] = args[1]
                    if exec_count > 0:
                        exec_count += len(args[1]) + 1
        except ValueError as e:
            raise pos_error(str(e), code, pos)
        if exec_count > 0:
            exec_count -= 1
            if exec_count == 0:
                exec_pos = None

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
