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

import ibe_ddl
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
            #self.__lines = [line for line in codecs.open(filename, encoding='cp1251')]
            self.__lines = [line for line in codecs.open(filename)]
            print(self.__lines)
            self.prepare_statements()
            #for statement in self.__statements:
            #    debug(statement)
        except IOError:
            print('Can\'t open the "{0}" file'.format(filename))

    def prepare_statements(self):
        term = ';'
        buf = ''
        comment = False
        for line in self.__lines[:]:
            line = line.strip()
            #debug(line)
            x = line.find('--')
            if -1 < x:
                line = line[:x]
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

            if ('' == line) or comment:
                continue
            buf = buf + line + ' '
            if term in buf.lower():
                buf = re.sub('[\t+\r+\n+]', ' ', buf).strip()
                buf = buf.replace('( ', '(')
                buf = buf.replace('  ', ' ')
                if buf.lower().startswith('insert'):
                    self.__statements.append(buf)
                else:
                    self.__statements.append(buf.lower())
                buf = ''
