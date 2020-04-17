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
from fractions import Fraction as frac

# Cheers interpreter by LegionMammal978
# see https://esolangs.org/wiki/Cheers

# notes:
# - strengths and volumes are rounded to integers for character output
# - at most 96 characters can be inputted at once; EOF results in a no-op
# - compound prepare statements prepare only one glass

def run(code):
    def try_match(pat, stmt):
        nonlocal match
        pat = pat.replace('_name_', r'([a-z-]+)')
        pat = pat.replace('_syrup_', r'([a-z-]+ syrup)')
        pat = pat.replace('_bev_', r'([a-z-]+(?: syrup)?)')
        pat = pat.replace('_vol_', r'((?:\d*\.)?\d+) ml')
        pat = pat.replace('_pct_', r'((?:\d*\.)?\d+)%')
        match = re.fullmatch(pat, stmt)
        return match is not None
    def same_ratios(layer1, layer2):
        if set(layer1.keys()) != set(layer2.keys()):
            return False
        vol1 = sum(layer1.values())
        vol2 = sum(layer2.values())
        for name in layer1.keys():
            if layer1[name] * vol2 != layer2[name] * vol1:
                return False
        return True
    def pour(gl1, gl2, vol, check=True):
        while len(gl1) > 0 and vol > 0:
            tlayer = gl1.pop()
            tv = sum(tlayer.values())
            if tv == 0:
                continue
            elif tv > vol:
                nlayer = tlayer.copy()
                for name in nlayer.keys():
                    tlayer[name] *= vol / tv
                    nlayer[name] *= 1 - vol / tv
                gl1.append(nlayer)
                add = vol
            else:
                add = tv
            if len(gl2) > 0 and same_ratios(gl2[-1], tlayer):
                nv = sum(gl2[-1].values())
                for name in tlayer.keys():
                    gl2[-1][name] *= 1 + add / nv
            else:
                gl2.append(tlayer)
            vol -= add
        tot = sum(sum(layer.values()) for layer in gl2)
        if check and tot > 500:
            pour(gl2, [], tot - 500, False)
    def mix(gl):
        if len(gl) == 0:
            return
        vmix = {}
        vol = frac(0)
        for layer in gl:
            for name, v in layer.items():
                if name in vmix:
                    vmix[name] += v
                else:
                    vmix[name] = v
        gl.clear()
        gl.append(vmix)
    stmts = re.split(r'\s*(?:[,;?!\n]|\.(?!\d))\s*', code.lower())
    stmts = [re.sub(r'\s+', ' ', stmt) for stmt in stmts]
    depth = 0
    for stmt in stmts:
        if stmt.endswith(' as') or stmt == 'binge':
            depth += 1
        elif stmt == 'end':
            if depth == 0:
                raise ValueError('too many end statements')
            depth -= 1
    if depth != 0:
        raise ValueError('missing end statements')
    ip = 0
    bevs = {'water': (False, frac(0))}
    match = None
    glass = []
    consumed = []
    prepstack = []
    intox = frac(0)
    clast = None
    while ip < len(stmts):
        if try_match('prepare drink _name_ _pct_', stmts[ip]):
            if match[1] == 'water':
                raise ValueError('prepare: water is a reserved name')
            if frac(match[2]) > 96:
                raise ValueError('prepare: invalid percentage')
            bevs[match[1]] = (False, frac(match[2]))
        elif try_match('prepare soft drink _name_', stmts[ip]):
            if match[1] == 'water':
                raise ValueError('prepare: water is a reserved name')
            bevs[match[1]] = (False, frac(0))
        elif try_match('prepare _syrup_', stmts[ip]):
            bevs[match[1]] = (False, frac(0))
        elif try_match('prepare water', stmts[ip]):
            pass
        elif try_match('prepare drink _name_ as', stmts[ip]):
            if match[1] == 'water':
                raise ValueError('prepare: water is a reserved name')
            prepstack.append([match[1], False, glass])
            glass = []
        elif try_match('pour fast _vol_ of _bev_', stmts[ip]):
            if len(prepstack) > 0 and prepstack[-1][0] != '_binge':
                prepstack[-1][1] = True
            vol = frac(match[1])
            if match[2] not in bevs:
                raise ValueError('pour: unrecognized beverage')
            if bevs[match[2]][0]:
                pour(bevs[match[2]][1], glass, vol)
            else:
                pour([{match[2]: vol}], glass, vol)
            mix(glass)
        elif try_match('pour slowly _vol_ of _bev_', stmts[ip]):
            if len(prepstack) > 0 and prepstack[-1][0] != '_binge':
                prepstack[-1][1] = True
            vol = frac(match[1])
            if match[2] not in bevs:
                raise ValueError('pour: unrecognized beverage')
            if bevs[match[2]][0]:
                pour(bevs[match[2]][1], glass, vol)
            else:
                pour([{match[2]: vol}], glass, vol)
        elif try_match('pour _vol_ of _bev_', stmts[ip]):
            speed = 'slowly' if match[2].endswith(' syrup') else 'fast'
            stmts[ip] = 'pour {} {} ml of {}'.format(speed, match[1], match[2])
            ip -= 1
        elif try_match('spill _vol_', stmts[ip]):
            pour(glass, [], frac(match[1]), False)
        elif try_match('cheers', stmts[ip]):
            for layer in glass:
                for name, v in layer.items():
                    intox += v * bevs[name][1] / 100
            pour(glass, consumed, 500, False)
        elif try_match('sip _vol_', stmts[ip]):
            temp = []
            pour(glass, temp, frac(match[1]), False)
            for layer in temp:
                for name, v in layer:
                    intox += v * bevs[name][1] / 100
            pour(temp, consumed, frac(match[1]), False)
        elif try_match('ask for a drink', stmts[ip]):
            if clast is None:
                clast = sys.stdin.read(1)
            if not clast:
                ip += 1
                continue
            n = frac(0)
            c = clast
            while n < 96 and clast == c:
                n += 1
                clast = sys.stdin.read(1)
                if not clast:
                    break
            name = '_in{}{}'.format(c, n)
            if name not in bevs:
                bevs[name] = (False, n)
            pour([{name: ord(c)}], glass, ord(c))
        elif try_match('throw up', stmts[ip]):
            for layer in consumed[::-1]:
                vol = sum(layer.values())
                volst = sum(v * bevs[name][1] for name, v in layer.items())
                n = round(volst / vol)
                c = chr(round(vol))
                sys.stdout.write(c * n)
            sys.stdout.flush()
            consumed.clear()
            intox = frac(0)
        elif try_match('binge', stmts[ip]):
            if intox >= 200:
                depth = 1
                while depth > 0:
                    ip += 1
                    if stmts[ip].endswith(' as') or stmts[ip] == 'binge':
                        depth += 1
                    elif stmts[ip] == 'end':
                        depth -= 1
            else:
                prepstack.append(['_binge', ip])
        elif try_match('end', stmts[ip]):
            frame = prepstack.pop()
            if frame[0] == '_binge':
                ip = frame[1] - 1
            elif not frame[1]:
                raise ValueError('prepare: missing pour statement')
            else:
                bevs[frame[0]] = (True, glass)
                glass = frame[2]
        elif try_match(r'mumble .*', stmts[ip]):
            pass
        elif stmts[ip] == '':
            pass
        else:
            raise ValueError('unrecognized statement: {}'.format(stmts[ip]))
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
