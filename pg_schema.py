#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PgSchema class load PostgreSQL dump to Schema class
#
#

import sys
import re
import codecs
import os

from os import path

from ibe_ddl import Schema
from ibe_ddl import Generator
from ibe_ddl import Domain
from ibe_ddl import Table
from ibe_ddl import StoredProcedure
from ibe_ddl import Trigger


def debug(msg):
    try:
        print(msg.encode(sys.stdout.encoding, errors='replace'))
    except TypeError:
        print("NONE")


class PgSchema(Schema):

    def __init__(self, filename):
        Schema.__init__(self)
        self.__lines = []
        self.__statements = []
        self.load(filename)

    def load(self, filename):
        try:
            # self.__lines = [line for line in codecs.open(filename, encoding='cp1251')]
            # print(filename)
            self.__lines = [line for line in codecs.open(filename)]
            # for line in self.__lines:
            #     print(line)
            self.__functions = {}
            self.prepare_statements()
            for statement in self.__statements:
                print(statement)

        except IOError:
            print('Can\'t open the "{0}" file'.format(filename))

    def prepare_statements(self):
        buf = ''
        comment = False
        func = False
        func_beg_cnt = 0
        func_end_cnt = 0
        for line in self.__lines[:]:
            line = line.strip()
            if 1 > len(line):
                continue

            if not func:
                if re.search('create function ', line, re.IGNORECASE):
                    # __functions[]
                    func = True
                    func_beg_cnt = 0
                    func_end_cnt = 0
                    continue
            else:
                if (-1 < line.find('$$')) or (-1 < line.find('$_$')):
                    if (0 == func_beg_cnt) or (func_beg_cnt < func_end_cnt):
                        func_beg_cnt = func_beg_cnt + 1
                    else:
                        func_end_cnt = func_end_cnt + 1

                # if re.search('begin ', line, re.IGNORECASE):
                #     func_beg_cnt = func_beg_cnt + 1
                # if re.search('end;', line, re.IGNORECASE):
                #     func_end_cnt = func_end_cnt + 1

            if func and (0 < func_beg_cnt) and (0 < func_end_cnt) and (func_beg_cnt == func_end_cnt):
                func = False
                continue

            if func:
                continue

            x = line.find('--')
            if -1 < x:
                line = line[:x]
            if 1 > len(line):
                continue
            x1 = line.find('/*')
            x2 = line.find('*/')
            if (-1 < x1) or (-1 < x2):
                if (-1 < x1) and (-1 < x2):
                    line = line[:x1] + line[x2 + 2:]
                else:
                    if -1 < x1:
                        line = line[:x1]
                        comment = True
                    else:
                        line = line[x2 + 2:]
                        comment = False

            if (1 > len(line)) or comment:
                continue

            # print('>> {} {}'.format(line, len(line)))

            buf = buf + line + ' '
            if ";" in buf.lower():
                print(buf)
                buf = re.sub("[\t+\r+\n+]", ' ', buf).strip()
                buf = buf.replace('( ', '(')
                buf = buf.replace('  ', ' ')

                if buf.lower().startswith('insert'):
                    self.__statements.append(buf)
                else:
                    self.__statements.append(buf.lower())
                buf = ''
