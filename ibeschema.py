#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# 
# This python script converts SQL-script writeen on Interbase/Firebird dialect
# to Microsoft Transact-SQL compatible script
# 
# Restrictions: 
#     - Don't use comma (;) char anywthere except statement delimiter (for example, in object descriptions)
#     - Use simple english database object names (without spaces, national characters, etc)
#     - Dont't use remote server connection string (like 192.168.47.38:/srv/firebird/moonhattan) in source script 
#
# 2013.03.14 [+] Check for "describe column", "comment on" statements
# 2013.03.13 [+] Timestamp column datatype changed to datetime for MSSQL
#                                GETDATE() used instead of "NOW" Firebird function
# 2013.01.01 [+] Initial release, base objects supported (database creation, domains, tables)
#                                Not yet support for views, stored procedures and triggers
#                                
# 
#

from ddl import Schema
from ddl import Generator
from ddl import Domain
from ddl import Table

import ddl
import sys
import re

def debug(msg):
    print(msg.encode(sys.stdout.encoding, errors='replace'))
    

def strip_localization(value):
    value = re.sub('character\s+set\s+\w+(\s+)?', ' ', value, re.IGNORECASE)
    value = re.sub('collate\s+\w+(\s+)?', ' ', value, re.IGNORECASE)
    value = ddl.strip_statement(value)
    return value


#
class IbeSchema(Schema):

    def __init__(self, filename):
        Schema.__init__(self)
        self.statements = []
        self.load(filename)

    def load(self, filename):
        try:
            #lines = [line.replace('\n', ' ') for line in open(infile)]
            #lines = [line.strip() for line in open(infile, encoding='utf-8')]
            lines = [line.strip() for line in open(filename)]
            self.prepare_statements(lines)
            self.parse_statements()
        except IOError as er:
            print('Can\'t open the "{0}" file'.format(filename))
            
    def prepare_statements(self, lines):
        re_set_term = re.compile('SET\s+TERM\s+?([;^])\s+?([;^])', re.IGNORECASE)
        term = ';'
        buf = ''
        comment = False
        i = 0
        for line in lines:
            m = re_set_term.search(line)
            if m is not None:
                term = m.group(1)
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
                if re_set_term.match(buf) is None:
                    buf = re.sub('[\t+\r+\n+]', ' ', buf).strip()
                    buf = buf.replace('( ', '(')
                    buf = buf.replace('  ', ' ')
                    if buf.lower().startswith('insert'):
                        self.statements.append(buf)
                    else:
                        self.statements.append(buf.lower())
                buf = ''

    def parse_generators(self):
        generators = {}

        re_gen1 = re.compile(
            'CREATE\s+GENERATOR\s+(.*);', re.IGNORECASE
        )
        re_gen2 = re.compile(
            'CREATE\s+TRIGGER\s+\w+\s+FOR\s+(\w+)\s+.*new\.([_\w]+)\s*=\s+gen_id\((\w+),\s+\d+\).*;?', re.IGNORECASE
        )
        for statement in self.statements[:]:
            
            m = re_gen1.search(statement)
            if m:
                gen_name = m.group(1).strip()
                gen = Generator(gen_name)
                generators[gen_name] = gen
                
            m = re_gen2.search(statement)
            if m:
                table_name = m.group(1).strip()
                field_name = m.group(2).strip()
                gen_name = m.group(3).strip()
                if gen_name in generators:
                    generators[gen_name].add_owner(table_name, field_name)
                else:
                    gen = Generator(gen_name)
                    gen.add_owner(table_name, field_name)
                    generators[gen_name] = gen

        for gen_name in generators:
            generator = generators[gen_name]
            self.generators.append(generator)

    def parse_domains(self):
        domains = {}
        re_dom = re.compile(
            'CREATE\s+DOMAIN\s+(\w+)\s+AS\s+(.*)?;', re.IGNORECASE
        )
        for statement in self.statements[:]:
            m = re_dom.search(statement)
            if m:
                dom_name = m.group(1)
                data_type = m.group(2).strip()
                data_type = strip_localization(data_type)
                autoinc = dom_name.endswith('_autoinc')
                domain = Domain(dom_name, data_type, autoinc)
                domains[dom_name] = domain
        for dom_name in domains:
            domain = domains[dom_name]
            self.domains.append(domain)


    def parse_views(self):
        self.views = []
        for statement in self.statements[:]:
            m = re.match('create\s+view\s+(.*)?;', statement, re.IGNORECASE)
            if m is not None:
                self.views.append(statement.rstrip(';').strip())

    def parse_tables(self):
        re_create_table = re.compile('create\s+table\s+(\w+)\s+\((.*)?\);', re.IGNORECASE)
        re_field = re.compile('(\w+)\s+(.*)', re.IGNORECASE)
        re_alter_table_pk = re.compile(
            'alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+primary\s+key\s+\((.*)\);', re.IGNORECASE)
        re_alter_table_fk = re.compile(
            'alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+foreign\s+key\s+\((.*)\)\s+'
            'references\s+(\w+)\s+\((\w+)\)\s?(on\s+delete\s+cascade)?\s?(on\s+update\s+cascade)?.*;', re.IGNORECASE)
        re_alter_table_uk = re.compile(
            'alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+unique\s+\((.*)\);', re.IGNORECASE)
        re_create_index = re.compile(
            'create\s?(unique|asc|ascending|desc|descending)?\s+index\s+(\w+)\s+on\s+(\w+)\s+\((.*)\);', re.IGNORECASE)
        for statement in self.statements:
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
                        field_type = strip_localization(field_type)
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

    def parse_procedures(self):
        self.procedures = []

    def parse_triggers(self):
        self.triggers = []

    def parse_statements(self):
        self.parse_generators()
        self.parse_domains()
        self.parse_views()
        self.parse_tables()
        self.parse_procedures()
        self.parse_triggers()

    def print_schema(self):
        for generator in self.generators:
            if 0 < len(generator.owners):
                for o in generator.owners:
                    print(generator.name + ' -> ' + o)
            else:
                print(generator.name)
        for domain in self.domains:
            if domain.autoinc:
                print(domain.name + ' -> ' + domain.data_type + ' ###')
            else:
                print(domain.name + ' -> ' + domain.data_type)
        for view in self.views:
            print(view)
        for table_name in self.tables:
            table = self.tables[table_name]
            t = table.name
            for field in table.fields:
                nullable = "not null"
                if field.nullable:
                    nullable = ""
                t += ' {0} {1} {2},'.format(field.name, field.data_type, nullable)
            print(t)
