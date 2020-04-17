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

# Noodle Soup interpreter by LegionMammal978
# see https://esolangs.org/wiki/Noodle_Soup

def run(code):
    code = re.sub('[^01]', '', code)
    ip = 0
    dp = 0
    data = [0]
    while True:
        if ip + 1 >= len(code):
            return
        elif code[ip : ip+2] == '10':
            data[dp] += 1
            if data[dp] == 256:
                data[dp] = 0
            ip += 2
        elif code[ip : ip+2] == '01':
            data[dp] -= 1
            if data[dp] == -1:
                data[dp] = 255
            ip += 2
        elif ip + 2 >= len(code):
            return
        elif code[ip : ip+3] == '111':
            dp += 1
            if dp == len(data):
                data.append(0)
            ip += 3
        elif code[ip : ip+3] == '000':
            dp -= 1
            if dp == -1:
                raise IndexError('moved past leftmost cell')
            ip += 3
        elif ip + 3 >= len(code):
            return
        elif code[ip : ip+4] == '1100':
            chin = sys.stdin.buffer.read(1)
            if chin:
                data[dp] = chin[0]
            else:
                data[dp] = 255
            ip += 4
        elif code[ip : ip+4] == '0011':
            sys.stdout.buffer.write(bytes([data[dp]]))
            sys.stdout.flush()
            ip += 4
        elif ip + 7 >= len(code):
            return
        elif code[ip : ip+4] == '1101':
            target = code[ip+4:ip+8] + '1011'
            inc = 1 if data[dp] == 0 else -1
            ip += inc
            while 0 <= ip <= len(code) - 8:
                if code[ip : ip+8] == target:
                    break
                ip += inc
            if ip < 0 or ip + 7 >= len(code):
                return
            ip += 8
        elif code[ip : ip+4] == '0010':
            target = code[ip+4:ip+8] + '0100'
            inc = -1 if data[dp] == 0 else 1
            ip += inc
            while 0 <= ip <= len(code) - 8:
                if code[ip : ip+8] == target:
                    break
                ip += inc
            if ip < 0 or ip + 7 >= len(code):
                return
            ip += 8

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
