#!/usr/bin/python
# -*- coding: utf-8 -*- 
#
# 2017-03-21 [i] extract sequential number array from string like "1...3,9..14, 17, 40, 41,57...77"
#                useful for "indie" project source files parse
#                Usage:
#                ...
#                import sys
#                sys.path.append('<path to tbd_num_list.py>')
#                import tbd_num_list
#                ...
#                a = num_list.get_num_list('1...3,9..14, 17, 40, 41,57...77')
#

import sys
import re

def get_num_list(value):
    # print(value)
    items = [item.replace(u'…', '...').replace(u' ', '') for item in value.split(',')]
    rval = []
    re_range = re.compile('(\d+)\.\.+(\d+)', re.IGNORECASE)
    for item in items:
        if '' == item.strip():
            continue
        if '-' == item.strip():
            continue
        if '--' == item.strip():
            continue
        elif item.isdigit():
              v = int(item)
              if not v in rval:
                  rval.append(int(item))
        else:
            m = re_range.match(item)
            if m is None:
                raise Exception('Unsupported item "' + item + '" for value "' + value + '"')
            if 2 <> len(m.groups()): 
                raise Exception('Wrong kind of groups for item "' + item + '" (' + str(len(m.groups())) + ') for value "' + value + '"')
            if not m.group(1).isdigit():
                raise Exception('Nondigit value "A" for item "' + item + '" for value "' + value + '"')
            if not m.group(2).isdigit():
                raise Exception('Nondigit value "B" for item "' + item + '" for value "' + value + '"')
            #print(m.group(1))
            #print(m.group(2))
            a = int(m.group(1))
            b = int(m.group(2))
            if b < a:
                raise Exception('"A" value (' + str(a) + ') lower when "B" (' + str(b) + ') for item "' + item + '" for value "' + value + '"')
            while a <= b:
                if not a in rval:
                    rval.append(a)
                a = a + 1

    return rval


def main(): 
    val = [
      '1,2,5...7,22,77...94'
    , '1,1,1...1'
    ,  u'1…10, 13…29, 34, 35, 36, 122...125'
    ,  u'1…10, 13…29, 34, 35, 36, 122...125'
    ,  u'317…..318'
    ,  u'-'
    ,  '--'
    ,  '  ' # empty string
    ]
    for v in val:
        print('\n')
        a = get_num_list(v)
        print(v)
        print(a)
       

if __name__ == "__main__":
    main()	
