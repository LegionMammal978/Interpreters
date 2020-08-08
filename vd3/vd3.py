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

# VD3 interpreter by LegionMammal978
# see https://esolangs.org/wiki/VD3
# note: -1 disables VD3 2.0 functionality

apat = '([A-E]|PC|IN|OUT|-?[0-9]+)'
cpat = fr'(\.{3})?([A-E]|PC|IN|OUT)<-{apat}\^{apat}\^{apat}'

def run(code, v1=False):
    def value(arg):
        if isinstance(arg, int):
            return arg
        elif arg in 'ABCDE':
            return vardict[arg]
        elif arg == 'PC':
            return ip
        elif arg == 'IN':
            chin = sys.stdin.buffer.read(1)
            return chin[0] if chin else -1
    cmds = []
    repeat = False
    for i, line in enumerate(code.split('\n')):
        if line == '':
            if repeat:
                cmds.append(cmds[-1])
            continue
        match = re.fullmatch(cpat, line)
        if match is None:
            raise ValueError('line {}: invalid format'.format(i + 1))
        match = match.groups()
        repeat = match[0] is not None
        if v1 and (repeat or any(arg in 'DE' for arg in match[1:])):
            raise ValueError('line {}: VD3 2.0 feature used'.format(i + 1))
        if match[1] == 'IN':
            raise ValueError('line {}: cannot write to IN'.format(i + 1))
        if 'OUT' in match[2:]:
            raise ValueError('line {}: cannot read from OUT'.format(i + 1))
        args = tuple(arg if arg.isalpha() else int(arg) for arg in match[1:])
        cmds.append(args)
    ip = 0
    vardict = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
    while True:
        if ip >= len(cmds) and repeat:
            cmd = cmds[-1]
        elif ip < 0 or ip >= len(cmds):
            return
        else:
            cmd = cmds[ip]
        total = sum(value(arg) for arg in cmd[1:])
        if cmd[0] in 'ABCDE':
            vardict[cmd[0]] = total
        elif cmd[0] == 'PC':
            ip = total - 1
        elif cmd[0] == 'OUT':
            if total < 0 or total > 255:
                raise ValueError('line {}: invalid character'.format(i + 1))
            sys.stdout.buffer.write(bytes([total]))
            sys.stdout.flush()
        ip += 1

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] == '-n' and len(sys.argv) < 3:
        print('usage: {} [-1] file'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(2)
    v1 = sys.argv[1] == '-1'
    with open(sys.argv[2 if v1 else 1], 'r') as f:
        code = f.read()
    try:
        run(code, v1)
    except Exception as e:
        print('error: {}'.format(e), file=sys.stderr)
        sys.exit(1)
