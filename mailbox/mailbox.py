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

# MailBox interpreter by LegionMammal978
# see https://esolangs.org/wiki/MailBox
# requires the lark-parser package from PyPI

# note: evaluation proceeds as follows:
# - all rules are evaluated in order of definition
# - if no rules evaluate to true and no messages are being processed,
#     the program exits
# - all applicable actions are evaluated in order of definition
# - if the message queue is not empty, a message is popped and the
#     receiving mailbox's message count is incremented

def run(code):
    parser = Lark(r'''
        prog  : box*
        box   : "box" INT "\n"+ rpair*
        rpair : "(" ror ")" "\n"+ (act "\n"+)*
        ?ror  : [ror "or"] rand
        ?rand : [rand "and"] rnot
        ?rnot : rpar | NOT rnot
        NOT   : "not"
        ?rpar : rbase | "(" ror ")"
        rbase : "true"                 -> true
              | "false"                -> false
              | "from" INT             -> is_from
              | "forwarded"            -> forwarded
              | "contains" STRING      -> contains
              | "contains" "count"     -> contains_count_self
              | "contains" "count" INT -> contains_count_other
              | "from" "count"         -> from_count_self
              | "from" "count" INT     -> from_count_other
              | "empty"                -> is_empty
              | "once"                 -> once
        act   : "send" STRING "to" INT                 -> send_to
              | "send" "count" STRING "to" INT         -> send_count_self_to
              | "send" STRING "to" "count"             -> send_to_count_self
              | "send" "count" INT STRING "to" INT     -> send_count_other_to
              | "empty"                                -> empty
              | "send" STRING "to" "count" INT         -> send_to_count_other
              | "forward" "to" INT                     -> forward_to
              | "forward" "to" INT "with" STRING       -> forward_to_with
              | "send" "count" INT STRING "to" "count" -> send_co_to_cs
              | "send" "count" STRING "to" "count" INT -> send_cs_to_co
              | "receive" "box" "number"               -> get_number
              | "output" "without" STRING              -> output_without
              | "output"                               -> output
              | "output" "count"                       -> output_count_self
              | "output" "count" INT                   -> output_count_other
              | "delete"                               -> delete
              | "send" "input" "to" INT                -> send_input_to

        %import common.ESCAPED_STRING -> STRING
        %import common.INT
        %import common.WS_INLINE
        %ignore WS_INLINE
        %ignore "//" /[^\n]/*
    ''', start='prog')
    class Parser(Transformer):
        def __init__(self):
            self.allpairs = []
            super().__init__()
        def STRING(self, tok):
            return re.sub(r'\\(.)', r'\1', tok[1:-1].replace(r'\n', '\n'))
        def INT(self, tok):
            return int(tok)
        def __default__(self, data, args, meta):
            return [data, *args]
        def once(self, args):
            return ['once', True]
        def rnot(self, args):
            return ['not', args[1]]
        def rpair(self, args):
            ret = {'rule': args[0], 'actions': args[1:]}
            self.allpairs.append(ret)
            return ret
        def box(self, args):
            ret = {'num': args[0], 'count': 0}
            for pair in args[1:]:
                pair['box'] = ret
            return ret
        def prog(self, args):
            boxes = {box['num']: box for box in args}
            return boxes, self.allpairs
    def eval_rule(rule, box, message):
        if rule[0] == 'true':
            return True, False
        if rule[0] == 'false':
            return False, False
        if rule[0] == 'and':
            arg1, recv1 = eval_rule(rule[1], box, message)
            if not arg1:
                return False, recv1
            arg2, recv2 = eval_rule(rule[2], box, message)
            return arg2, recv1 or recv2
        if rule[0] == 'or':
            arg1, recv1 = eval_rule(rule[1], box, message)
            if arg1:
                return True, recv1
            arg2, recv2 = eval_rule(rule[2], box, message)
            return arg2, recv1 or recv2
        if rule[0] == 'not':
            arg, recv = eval_rule(rule[1], box, message)
            return not arg, recv
        if rule[0] == 'empty':
            return box['count'] == 0, False
        if rule[0] == 'once':
            temp, rule[1] = rule[1], False
            return temp, False
        if message is None or message['to'] != box['num']:
            return False, False
        if rule[0] == 'is_from':
            return message['from'] == rule[1], True
        if rule[0] == 'forwarded':
            return message['forwarded'], True
        if rule[0] == 'contains':
            return rule[1] in message['subject'], True
        if rule[0] == 'contains_count_self':
            return str(box['count']) in message['subject'], True
        if rule[0] == 'contains_count_other':
            return str(boxes[rule[1]]['count']) in message['subject'], True
        if rule[0] == 'from_count_self':
            return message['from'] == box['count'], True
        if rule[0] == 'from_count_other':
            return message['from'] == boxes[rule[1]]['count'], True
    def eval_action(action, box, message, recv):
        if action[0] == 'send_to':
            messages.append({
                'from': box['num'],
                'to': action[2],
                'subject': action[1],
                'forwarded': False
            })
        elif action[0] == 'send_count_self_to':
            for _ in range(box['count']):
                messages.append({
                    'from': box['num'],
                    'to': action[2],
                    'subject': action[1],
                    'forwarded': False
                })
        elif action[0] == 'send_to_count_self':
            messages.append({
                'from': box['num'],
                'to': box['count'],
                'subject': action[1],
                'forwarded': False
            })
        elif action[0] == 'send_count_other_to':
            for _ in range(boxes[action[1]]['count']):
                messages.append({
                    'from': box['num'],
                    'to': action[3],
                    'subject': action[2],
                    'forwarded': False
                })
        elif action[0] == 'empty':
            box['count'] = 0
        elif action[0] == 'send_to_count_other':
            messages.append({
                'from': box['num'],
                'to': boxes[action[2]]['count'],
                'subject': action[1],
                'forwarded': False
            })
        elif action[0] == 'send_co_to_cs':
            for _ in range(boxes[action[1]]['count']):
                messages.append({
                    'from': box['num'],
                    'to': box['count'],
                    'subject': action[2],
                    'forwarded': False
                })
        elif action[0] == 'send_cs_to_co':
            for _ in range(box['count']):
                messages.append({
                    'from': box['num'],
                    'to': boxes[action[2]]['count'],
                    'subject': action[1],
                    'forwarded': False
                })
        elif action[0] == 'get_number':
            box['count'] += box['num']
        elif action[0] == 'output_count_self':
            print(box['count'])
        elif action[0] == 'output_count_other':
            print(boxes[action[1]]['count'])
        elif action[0] == 'delete' and box['count'] != 0:
            box['count'] -= 1
        elif action[0] == 'send_input_to':
            messages.append({
                'from': box['num'],
                'to': action[1],
                'subject': sys.stdin.readline().rstrip('\n'),
                'forwarded': False
            })
        elif not recv:
            return
        elif action[0] == 'forward_to':
            messages.append({
                'from': box['num'],
                'to': action[1],
                'subject': message['subject'],
                'forwarded': True
            })
        elif action[0] == 'forward_to_with':
            messages.append({
                'from': box['num'],
                'to': action[1],
                'subject': message['subject'] + action[2],
                'forwarded': True
            })
        elif action[0] == 'output_without':
            print(message['subject'].replace(action[1], ''))
        elif action[0] == 'output':
            print(message['subject'])
    boxes, allpairs = Parser().transform(parser.parse(code + '\n'))
    messages = []
    message = None
    while True:
        actions = []
        for pair in allpairs:
            val, recv = eval_rule(pair['rule'], pair['box'], message)
            if not val:
                continue
            for action in pair['actions']:
                actions.append((action, pair['box'], recv))
        if message is None and len(actions) == 0:
            break
        for action, box, recv in actions:
            eval_action(action, box, message, recv)
        if len(messages) > 0:
            message = messages.pop(0)
            boxes[message['to']]['count'] += 1
        else:
            message = None

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
