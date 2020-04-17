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

# Duck Duck Goose interpreter by LegionMammal978
# see https://esolangs.org/wiki/Duck_Duck_Goose

def run(code):
    def d(n, check=True):
        if n % len(ducks) == 0:
            raise IndexError('line {}: invalid duck'.format(ip + 1))
        return (n + g) % len(ducks)
    lines = re.sub('#.*', '', code).lower().split('\n')
    inputs = []
    for i, line in enumerate(lines):
        cmds = re.findall('duck|goose', line)
        if set(cmds) in (set(), {'duck'}):
            if i == 0:
                raise ValueError('line 1: invalid header')
            inputs.append(len(cmds))
            lines[i] = [-1]
        elif cmds[-1] != 'goose' or set(cmds[:-1]) not in (set(), {'duck'}):
            if i == 0:
                raise ValueError('line 1: invalid header')
            else:
                raise ValueError('line {}: invalid command'.format(i + 1))
        elif i == 0:
            lines[i] = [len(cmds)]
        elif len(cmds) == 1:
            if len(inputs) > 0:
                raise ValueError('line {}: too many inputs'.format(i + 1))
            lines[i] = [0]
        elif len(cmds) in (2, 7, 8, 9, 11):
            if len(inputs) < 1:
                raise ValueError('line {}: too few inputs'.format(i + 1))
            if len(inputs) > 1:
                raise ValueError('line {}: too many inputs'.format(i + 1))
            lines[i] = [len(cmds) - 1, *inputs]
            inputs.clear()
        elif len(cmds) in (3, 4, 5, 6, 10, 12):
            if len(inputs) < 2:
                raise ValueError('line {}: too few inputs'.format(i + 1))
            if len(inputs) > 2:
                raise ValueError('line {}: too many inputs'.format(i + 1))
            lines[i] = [len(cmds) - 1, *inputs]
            inputs.clear()
        else:
            raise ValueError('line {}: unknown command'.format(i + 1))
    if set(inputs) not in (set(), {0}):
        raise ValueError('unused inputs')
    labels = {}
    for i, line in enumerate(lines):
        if i == 0:
            continue
        elif line[0] == 9:
            if line[2] in labels:
                raise ValueError('line {}: duplicate label'.format(i + 1))
            labels[line[2]] = [i, None]
        elif line[0] == 10:
            if line[1] not in labels:
                raise ValueError('line {}: nonexistent label'.format(i + 1))
            if labels[line[1]][1] is not None:
                raise ValueError('line {}: loop already ended'.format(i + 1))
            labels[line[1]][1] = i
    if any(end is None for start, end in labels.values()):
        raise ValueError('unclosed loop')
    ducks = [0] * lines[0][0]
    tchr = 0
    g = 0
    ip = 1
    while ip < len(lines):
        line = lines[ip]
        cmd = line[0]
        if len(line) > 1:
            n = line[1]
        if len(line) > 2:
            y = line[2]
        if cmd == 0:
            sys.exit()
        elif cmd == 1:
            sys.stdout.write(chr(ducks[d(n)]))
        elif cmd == 2:
            ducks[g] = ducks[d(n)] + ducks[d(y)]
            g = d(n, False)
        elif cmd == 3:
            ducks[g] = ducks[d(n)] - ducks[d(y)]
            g = d(n, False)
        elif cmd == 4:
            ducks[g] = ducks[d(n)] * ducks[d(y)]
            g = d(n, False)
        elif cmd == 5:
            nv, yv = ducks[d(n)], ducks[d(y)]
            ducks[g] = nv//yv if nv*yv > 0 else -(-nv//yv)
            g = d(n, False)
        elif cmd == 6:
            inc = sys.stdin.read(1)
            ducks[g] = ord(inc) if inc != '' else 0
            g = d(n, False)
        elif cmd == 7:
            ducks[g] = ducks[d(n)]
            tchr = ducks[d(n)]
            g = d(n, False)
        elif cmd == 8:
            ducks[0] = tchr
            tchr = 0
            g = d(n, False)
        elif cmd == 9 and ducks[d(n)] == 0:
            ip = labels[y][1]
        elif cmd == 10:
            ip = labels[n][0] - 1
        elif cmd == 11:
            ducks[g] = y
            g = d(n, False)
        ip += 1
    raise ValueError('missing end command')

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
