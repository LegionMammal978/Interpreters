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

import codecs
import re
import sys

# Pizza Delivery interpreter by LegionMammal978
# see https://esolangs.org/wiki/Pizza_Delivery

def run(code):
    blocks = {}
    blstack = []
    ip = 0
    iscomm = False
    while ip < len(code):
        if iscomm:
            iscomm = code[ip] != '#'
        elif code[ip] == '#':
            iscomm = True
        elif code[ip] in '[(':
            blstack.append(ip)
        elif code[ip] == ']':
            if len(blstack) == 0:
                raise ValueError('too many ] statements')
            stip = blstack.pop()
            blocks[stip] = ip
            blocks[ip] = stip - 1
        ip += 1
    if len(blstack) > 0:
        raise ValueError('missing ] statements')
    sq = [[0]*16 for _ in range(16)]
    lx, ly = 0, 0
    ip = 0
    iswhile, iscomm = True, False
    while ip < len(code):
        cmd = code[ip]
        if iscomm:
            if cmd == '#':
                iscomm = False
            ip += 1
            continue
        if cmd in '0123456789ABCDEF':
            num = ''
            while ip < len(code):
                cmd = code[ip]
                if cmd not in '0123456789ABCDEF':
                    break
                num += cmd
                ip += 1
            else:
                return
            sq[lx][ly] = int(num, 16) % 256
        while cmd == '@':
            cmd = chr(sq[lx][ly])
            if cmd in '[(]#':
                raise ValueError('invalid @ output {}'.format(cmd))
        if cmd in '0123456789ABCDEF':
            sq[lx][ly] = int(cmd, 16)
        elif cmd in 'wasdqezc':
            lx += (cmd in 'dec') - (cmd in 'aqz')
            ly += (cmd in 'szc') - (cmd in 'wqe')
            if not (0 <= lx < 16 and 0 <= ly < 16):
                raise IndexError('pointer ran off of square')
        elif cmd == '?':
            chin = sys.stdin.buffer.read(1)
            sq[lx][ly] = chin[0] if chin else 255
        elif cmd == '`':
            sys.stdout.buffer.write(bytes([sq[lx][ly]]))
            sys.stdout.flush()
        elif cmd == '+':
            sq[lx][ly] = (sq[lx][ly]+1) % 256
        elif cmd == '-':
            sq[lx][ly] = (sq[lx][ly]-1) % 256
        elif cmd == '*':
            sq[lx][ly] = 2*sq[lx][ly] % 256
        elif cmd == ':':
            ip += 1
            if ip == len(code):
                raise ValueError('incomplete : statement')
            cmd = code[ip]
            if cmd == 'P':
                l = sq[lx][ly]
                if l % 2 == 0 or l < 2:
                    sq[lx][ly] = int(l == 2)
                else:
                    c = any(l % i == 0 for i in range(3, int(l**.5) + 1, 2))
                    sq[lx][ly] = int(not c)
            elif cmd == 'E':
                sq[lx][ly] %= 2
            elif cmd == 'R':
                sq[lx][ly] = ord(codecs.encode(chr(sq[lx][ly]), 'rot_13'))
            else:
                raise ValueError('unrecognized statement :{}'.format(cmd))
        elif cmd == '.':
            return
        elif cmd in '/\\' or cmd.isspace():
            pass
        elif cmd == '[':
            if sq[lx][ly] == 0:
                ip = blocks[ip]
        elif cmd == '(':
            if sq[lx][ly] > 0:
                ip = blocks[ip]
        elif cmd == ']':
            if iswhile:
                ip = blocks[ip]
        elif cmd == '{':
            iswhile = not iswhile
        else:
            raise ValueError('unrecognized statement {}'.format(cmd))
        ip += 1

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
