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

# Varsig interpreter by LegionMammal978
# see https://esolangs.org/wiki/Varsig

def run(code):
    def parsenum(s):
        if s.isalpha():
            i = ord(s) - 65
            varread[i] = True
            return var[i]
        else:
            return int(s)
    syms = {
        'SIG': '{', 'TERM': '}', 'MEASURE': '"', 'TRIP': '^', 'RESET': '.',
        'PRY': '(', 'CRAM': ')', 'EXIT': '#', 'LESS': '<', 'MORE': '>',
        'GOOD': '=', 'EVIL': '?', 'CLEAN': '_', 'DIRTY': '&', 'GROW': '+',
        'SHRINK': '-', 'PURGE': r'\\', 'BURN': '|', 'SHOVE': '!', 'YANK': '~',
        'CLONE': ':', 'PUSH': ']', 'PULL': '[', 'FLIP': '%'
    }
    code = re.sub(r'/\*(?:[^*]|\*[^/])*\*/', '', code)
    for name, sym in syms.items():
        code = re.sub(r'\b{}\b'.format(name), sym, code)
    code = re.sub(r'\s', '', code)
    if re.search('[&<-?_]$', code):
        raise ValueError('unterminated conditional command')
    if re.search('[&<-?_][{}]', code):
        raise ValueError('signal blocks cannot be conditional')
    cmd_regex = r'[!"+.[\]^{-](?:[A-Z]|[0-9]+)|[!#%&()+:<-?[-\]_|}~-]'
    cmds = re.findall(cmd_regex, code)
    if sum(len(cmd) for cmd in cmds) != len(code):
        inval = ''.join(re.split(cmd_regex, code))
        raise ValueError('unrecognized characters {}'.format(inval))
    ctrip = set()
    ntrip = set()
    sigs = {}
    stack = []
    tape = [[0, 0]]
    ip = 0
    tp = 0
    tf = False
    var = [0]*26
    varread = [False]*26
    measure = 256
    while ip < len(cmds):
        if cmds[ip][0] == '{':
            stack.append(ip)
        elif cmds[ip][0] == '}':
            if len(stack) == 0:
                raise ValueError('too many TERM commands')
            sigs[stack.pop()] = ip
        ip += 1
    if len(stack) > 0:
        raise ValueError('too few TERM commands')
    ip = 0
    while True:
        cmd = cmds[ip]
        num = parsenum(cmd[1:]) if len(cmd) > 1 else None
        if cmd[0] == '{' and num not in ctrip:
            ip = sigs[ip]
        elif cmd[0] == '"':
            measure = 2**num
            for i in range(len(stack)):
                stack[i] %= measure
            for i in range(len(tape)):
                tape[i][0] %= measure
                tape[i][1] %= measure
        elif cmd[0] == '^':
            ntrip.add(num)
        elif cmd[0] == '.':
            ntrip.remove(num)
        elif cmd[0] == '(':
            chin = sys.stdin.buffer.read(1)
            if chin:
                stack.append(chin[0] % measure)
        elif cmd[0] == ')' and len(stack) > 0:
            sys.stdout.buffer.write(bytes([stack.pop() % 256]))
            sys.stdout.flush()
        elif cmd[0] == '#':
            break
        elif (cmd[0] in '<>&' and len(stack) == 0 or
              cmd[0] == '_' and len(stack) > 0 or
              cmd[0] == '<' and tape[tp][tf] >= stack[-1] or
              cmd[0] == '>' and tape[tp][tf] <= stack[-1] or
              cmd[0] == '=' and len(stack) > 0 and tape[tp][tf] != stack[-1] or
              cmd[0] == '?' and len(stack) > 0 and tape[tp][tf] == stack[-1]):
            while cmds[ip][0] in '<>=?_&':
                ip += 1
        elif cmd[0] == '+' and (num is not None or len(stack) > 0):
            tape[tp][tf] += stack.pop() if num is None else num
            tape[tp][tf] %= measure
        elif cmd[0] == '-' and (num is not None or len(stack) > 0):
            tape[tp][tf] -= stack.pop() if num is None else num
            tape[tp][tf] %= measure
        elif cmd[0] == '\\':
            tape[tp][tf] = 0
        elif cmd[0] == '|' and len(stack) > 0:
            stack.pop()
        elif cmd[0] == '!':
            stack.append(tape[tp][tf] if num is None else num % measure)
        elif cmd[0] == '~' and len(stack) > 0:
            tape[tp][tf] = stack.pop()
        elif cmd[0] == ':' and len(stack) > 0:
            stack.append(stack[-1])
        elif cmd[0] == ('[' if tf else ']'):
            if num is None:
                num = 1
            if tp < num:
                for _ in range(num - tp):
                    tape.insert(0, [0, 0])
                tp = 0
            else:
                tp -= num
        elif cmd[0] == (']' if tf else '['):
            tp += 1 if num is None else num
            while tp >= len(tape):
                tape.append([0, 0])
        elif cmd[0] == '%':
            tf = not tf
        ip += 1
        if ip == len(cmds):
            ip = 0
            ctrip = ntrip
            ntrip = set()
            for i in range(26):
                var[i] += varread[i]
                varread[i] = False

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
