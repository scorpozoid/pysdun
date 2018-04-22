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


def strip_nextval(value):
    value = re.sub('default\s+nextval\(.*\)', '', value, re.IGNORECASE)
    return value

    # default nextval('public.sound_gen'::regclass)

class PgSchema(Schema):

    def __init__(self, filename):
        Schema.__init__(self)
        self.__lines = []
        self.__statements = []
        self.__functions = {}
        self.alias = '{{alias}}'
        self.load(filename)

    def load(self, filename):
        try:
            self.__lines = [line for line in codecs.open(filename)]
            self.prepare_statements()
            self.prepare_functions()
            self.parse_tables()
            self.parse_domains()
            self.parse_views()
            self.parse_triggers()

        except IOError:
            print('Can\'t open the "{0}" file'.format(filename))

    def prepare_statements(self):
        buf = ''
        comment = False
        func = False
        func_beg_cnt = 0
        func_end_cnt = 0
        func_name = None
        for line in self.__lines[:]:
            temp_line = line.replace('\r', '').replace('\n', '')
            if 1 > len(temp_line.strip()):
                continue

            if not func:
                m = re.search('create function (.*)?\(.*', line, re.IGNORECASE);
                if m:
                    func_name = m.group(1)
                    if func_name:
                        func_name = func_name.replace('public.', '')
                        self.__functions[func_name] = []
                        self.__functions[func_name].append(line)
                    else:
                        print('WARNING! NONAME FUNCTION!')
                    func = True
                    func_beg_cnt = 0
                    func_end_cnt = 0
                    continue
            else:
                if func_name in self.__functions:
                    self.__functions[func_name].append(line)
                if (-1 < line.find('$$')) or (-1 < line.find('$_$')):
                    if (0 == func_beg_cnt) or (func_beg_cnt < func_end_cnt):
                        func_beg_cnt = func_beg_cnt + 1
                    else:
                        func_end_cnt = func_end_cnt + 1
                if (0 < func_beg_cnt) and (0 < func_end_cnt) and (func_beg_cnt == func_end_cnt):
                    func = False
                    func_name = None
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
                buf = re.sub("[\t+\r+\n+]", ' ', buf).strip()
                buf = buf.replace('( ', '(')
                buf = buf.replace('  ', ' ')
                buf = buf.replace(' public.', ' ')

                if buf.lower().startswith('insert'):
                    self.__statements.append(buf)
                else:
                    buf = buf.lower().replace(' using btree', '')
                    self.__statements.append(buf)
                # print(buf)
                buf = ''

    def prepare_functions(self):
        for func_name in self.__functions:
            func = StoredProcedure(func_name)
            body = self.__functions[func_name]
            for line in body:
                func.body.append('-- ' + line)
            self.procedures.append(func)

    def parse_domains(self):
        domains = {}
        re_dom = re.compile(
            'CREATE\s+DOMAIN\s+([\w\.]+)\s+AS\s+(.*);', re.IGNORECASE
        )
        for statement in self.__statements[:]:
            m = re_dom.search(statement)
            if m:
                try:
                    dom_name = m.group(1)
                    data_type = m.group(2).strip()
                    data_type = strip_nextval(data_type)
                    autoinc = dom_name.endswith('_autoinc') or dom_name.endswith('sequence_t')
                    domain = Domain(dom_name, data_type, autoinc)
                    domains[dom_name] = domain
                except:
                    print('Error parse "' + statement + '"')
        for dom_name in domains:
            domain = domains[dom_name]
            self.domains.append(domain)


    def parse_tables(self):
        re_create_table = re.compile('create\s+table\s+(\w+)\s+\((.*)?\);', re.IGNORECASE)
        re_field = re.compile('(\w+)\s+(.*)', re.IGNORECASE)
        re_alter_table_pk = re.compile(
            'alter\s+table\s+only\s+(\w+)\s+add\s+constraint\s+(\w+)\s+primary\s+key\s+\((.*)\);', re.IGNORECASE)
        re_alter_table_fk = re.compile(
            'alter\s+table\s+only\s+(\w+)\s+add\s+constraint\s+(\w+)\s+foreign\s+key\s+\(([\w\_]+)\)\s+'
            'references\s+([\w\_]+)\s*\(([\w\_]+)\)\s?(on\s+update\s+cascade)?\s?(on\s+delete\s+cascade)?;', re.IGNORECASE)
        re_alter_table_uk = re.compile(
            'alter\s+table\s+only\s+(\w+)\s+add\s+constraint\s+(\w+)\s+unique\s+\((.*)\);', re.IGNORECASE)
        re_create_index = re.compile(
            'create\s?(unique|asc|ascending|desc|descending)?\s+index\s+(\w+)\s+on\s+(\w+)\s+\((.*)\);', re.IGNORECASE)
        for statement in self.__statements[:]:
            mt = re_create_table.match(statement)
            if mt is not None:
                table_name = mt.group(1)
                field_items = mt.group(2)
                field_list = map(lambda s: s.strip(' \t\n\r'), field_items.split(','))
                table = Table(table_name, "")
                for field in field_list:
                    mf = re_field.match(field)
                    if mf is not None:
                        field_name = mf.group(1)
                        field_type = mf.group(2)
                        nullable = True
                        if "not null" in field_type:
                            field_type = field_type.replace("not null", '')
                            nullable = False
                        field_type = strip_nextval(field_type)
                        table.add_field(field_name, field_type, nullable, "")
                if not table_name in self.tables:
                    self.tables[table_name] = table
                continue
            #
            mpk = re_alter_table_pk.match(statement)
            if mpk is not None:
                table_name = mpk.group(1)
                key_name = mpk.group(2)
                field_items = mpk.group(3)
                field_list = [item.strip() for item in field_items.split(',')]
                self.tables[table_name].add_pk(key_name, list(field_list))
                continue
            #
            mfk = re_alter_table_fk.match(statement)
            if mfk is not None:
                table_name = mfk.group(1)
                key_name = mfk.group(2)
                field_items = mfk.group(3)
                ref_table_name = mfk.group(4)
                ref_field_items = mfk.group(5)
                del_rule = mfk.group(6)
                upd_rule = mfk.group(7)
                field_list = [item.strip() for item in field_items.split(',')]
                ref_field_list = [item.strip() for item in ref_field_items.split(',')]
                if del_rule is None:
                    del_rule = "on delete no action"
                else:
                    del_rule = del_rule.strip()
                if upd_rule is None:
                    upd_rule = "on update no action"
                else:
                    upd_rule = upd_rule.strip()
                self.tables[table_name].add_fk(key_name, field_list, ref_table_name, ref_field_list, del_rule, upd_rule);
                continue

            muk = re_alter_table_uk.match(statement)
            if muk is not None:
                table_name = muk.group(1)
                key_name = muk.group(2)
                field_items = muk.group(3)
                field_list = [item.strip() for item in field_items.split(',')]
                self.tables[table_name].add_uk(key_name, field_list)
                continue

            mx = re_create_index.match(statement)
            if mx is not None:
                table_name = mx.group(3)
                index_name = mx.group(2)
                order = mx.group(1)
                field_items = mx.group(4)
                unique = None
                if order is not None:
                    order = order.lower().strip()
                    if order.startswith('asc'):
                        order = "asc"
                    elif order.startswith('desc'):
                        order = "desc"
                    elif order.startswith('uniq'):
                        order = ""
                        unique = "unique"
                    else:
                        order = "asc"
                else:
                    order = "asc"
                field_list = [item.strip() for item in field_items.split(',')]
                self.tables[table_name].add_index(index_name, field_list, order, unique)
                continue

    def parse_views(self):
        self.views = []
        for statement in self.__statements[:]:
            m = re.match('create\s+view\s+(.*)?;', statement, re.IGNORECASE)
            if m is not None:
                self.views.append(statement.rstrip(';').strip())

    def parse_triggers(self):
        self.triggers = []
        rep_create_trigger = \
          'create\s+trigger\s+(?P<p_tr_name>\w+)\s+(?P<p_tr_place>(before|after)\s+(insert|update|delete))\s+' \
          'on\s+(?P<p_table_name>\w+)\s+for\s+each\s+(?P<p_range>row|statement)\s+execute\s+procedure\s+(?P<p_func>\w+)'
        re_create_trigger = re.compile(rep_create_trigger, re.IGNORECASE)
        for statement in self.__statements[:]:
            m = re_create_trigger.match(statement)
            if m is not None:
                groups = m.groupdict()
                if "p_tr_name" in groups:
                    tr_name = groups["p_tr_name"].strip()
                else:
                    tr_name = ''
                if "p_table_name" in groups:
                    table_name = groups["p_table_name"].strip()
                else:
                    table_name = ''
                if "p_tr_place" in groups:
                    tr_place = groups["p_tr_place"].strip()
                else:
                    tr_place = ''
                if "p_tr_position" in groups:
                    tr_pos = groups["p_tr_position"]
                else:
                    tr_pos = ''
                if "p_func" in groups:
                    tr_func = groups["p_func"]
                else:
                    tr_func = ''

                tr = Trigger(tr_name)
                tr.table = table_name
                tr.place = tr_place
                tr.position = tr_pos
                if tr_func in self.__functions:
                    for line in self.__functions[tr_func]:
                        tr.body.append('-- ' + line)

                self.triggers.append(tr)
