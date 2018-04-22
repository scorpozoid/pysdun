#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# 
# IbeSchema class load SQL-script written on Interbase/Firebird dialect to Schema class
#
# Restrictions:
#     - Don't use comma (;) char anywhere except statement delimiter (for example, in object descriptions)
#     - Use simple english database object names (without spaces, national characters, etc)
#     - [seems fixed] Don't use remote server connection string (like 192.168.47.38:/srv/firebird/moonhattan) in source script
#
# 2013.03.14 [+] Check for "describe column", "comment on" statements
# 2013.03.13 [+] Timestamp column data type changed to datetime for MSSQL
#                                GETDATE() used instead of "NOW" Firebird function
# 2013.01.01 [+] Initial release, base objects supported (database creation, domains, tables)
#                                Not yet support for views, stored procedures and triggers
#                                
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
    print(msg.encode(sys.stdout.encoding, errors='replace'))
    

def strip_localization(value):
    value = re.sub('character\s+set\s+\w+(\s+)?', ' ', value, re.IGNORECASE)
    value = re.sub('collate\s+\w+(\s+)?', ' ', value, re.IGNORECASE)
    value = ibe_ddl.strip_statement(value)
    return value


#
class IbeSchema(Schema):

    def __init__(self, filename):
        Schema.__init__(self)
        self.__re_set_term = None
        self.__lines = []
        self.__statements = []
        self.load(filename)

    def load(self, filename):
        try:
            #self.__lines = [line for line in open(filename)]
            #self.__lines = [line.strip() for line in open(filename, encoding='utf-8')]
            #self.__lines = [line.strip() for line in open(filename, encoding='cp1251')]
            self.__lines = [line for line in codecs.open(filename, encoding='cp1251')]

            self.prepare_statements()
            self.parse_statements()
            self.overwrite_sp_bodies()
            self.overwrite_tr_bodies()
        except IOError as er:
            print('Can\'t open the "{0}" file'.format(filename))

    def replace_term(self, statement, term):
        if self.__re_set_term is None:
            self.__re_set_term = re.compile('set\s+term\s+?([;^])\s+?([;^])', re.IGNORECASE)
        m = self.__re_set_term.match(statement)
        if m is not None:
            term = m.group(1)
        return term

    def prepare_statements(self):
        term = ';'
        buf = ''
        comment = False
        i = 0
        # stripped_lines = (line.strip() for line in self.__lines[:])
        for line in self.__lines[:]:
            line = line.strip()
            term = self.replace_term(line, term)
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
                if self.__re_set_term.match(buf) is None:
                    buf = re.sub('[\t+\r+\n+]', ' ', buf).strip()
                    buf = buf.replace('( ', '(')
                    buf = buf.replace('  ', ' ')
                    if buf.lower().startswith('insert'):
                        self.__statements.append(buf)
                    else:
                        self.__statements.append(buf.lower())
                buf = ''

    def parse_generators(self):
        generators = {}

        re_gen1 = re.compile(
            'CREATE\s+GENERATOR\s+(.*);', re.IGNORECASE
        )
        re_gen2 = re.compile(
            'CREATE\s+TRIGGER\s+\w+\s+FOR\s+(\w+)\s+.*new\.([_\w]+)\s*=\s+gen_id\((\w+),\s+\d+\).*;?', re.IGNORECASE
        )
        for statement in self.__statements[:]:
            
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
            #'CREATE\s+DOMAIN\s+(\w+)\s+AS\s+(?:.*);', re.IGNORECASE
        )
        for statement in self.__statements[:]:
            m = re_dom.search(statement)
            if m:
                try:
                    dom_name = m.group(1)
                    data_type = m.group(2).strip()
                    data_type = strip_localization(data_type)
                    autoinc = dom_name.endswith('_autoinc') or dom_name.endswith('sequence_t')
                    domain = Domain(dom_name, data_type, autoinc)
                    domains[dom_name] = domain
                except:
                    print('Error parse "' + statement + '"')
        for dom_name in domains:
            domain = domains[dom_name]
            self.domains.append(domain)


    def parse_views(self):
        self.views = []
        for statement in self.__statements[:]:
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

    # def parse_procedures(self):
    #     self.procedures = []
    #     g_sp_name = 'g_sp_name'
    #     g_sp_in = 'g_sp_in'
    #     g_sp_out = 'g_sp_out'
    #     g_sp_body = 'g_sp_body'
    #     rep_alter_sp = \
    #         'alter\s+procedure\s+(?P<{}>\w+)' \
    #         '\s*(?:\((?P<{}>.*)\)*)' \
    #         '\s*(?:RETURNS\s*\((?P<{}>.*)\)*)' \
    #         '\s*as(?P<{}>.*)?;'.format(
    #         g_sp_name, g_sp_in, g_sp_out, g_sp_body
    #     )
    #     re_alter_sp = re.compile(rep_alter_sp, re.IGNORECASE)
    #
    #     for statement in self.__statements[:]:
    #         m = re_alter_sp.match(statement)
    #         if m is not None:
    #             groups = m.groupdict()
    #             # sp = StoredProcedure(groups[g_sp_name], groups[g_sp_in], groups[g_sp_out], groups[g_sp_body])
    #             if g_sp_name in groups:
    #                 sp_name = groups[g_sp_name]
    #             else:
    #                 sp_name = ''
    #             if g_sp_in in groups:
    #                 sp_in = groups[g_sp_in]
    #             else:
    #                 sp_in = ''
    #             if g_sp_out in groups:
    #                 sp_out = groups[g_sp_out]
    #             else:
    #                 sp_out = ''
    #             if g_sp_body in groups:
    #                 sp_body = groups[g_sp_body]
    #             else:
    #                 sp_body = ''
    #             sp = StoredProcedure(sp_name, sp_in, sp_out, sp_body)
    #             self.procedures.append(sp)
    #             print('***' + sp.name + ' & ' + sp.pm_in + ' & ' + sp.pm_out + ' & ' + sp.body)
    #     #re_alter_sp = re.compile('create\s+table\s+(\w+)\s+\((.*)?\);', re.IGNORECASE)

    def overwrite_sp_bodies(self):
        term = ';'
        for sp in self.procedures:
            found = False
            sp_body = []
            for line in self.__lines[:]:
                if not found:
                    term = self.replace_term(line, term)
                    rep = 'alter\s+procedure\s+{}'.format(sp.name)
                    m = re.match(rep, line, re.IGNORECASE)
                    if m is not None:
                        found = True
                if found:
                    sp_body.append(line.rstrip())
                    rep_end = "end\s*\\{}".format(term)
                    if re.match(rep_end, line, re.IGNORECASE):
                        found = False
                        break
                    if line.strip() == term:
                        found = False
                        break
            sp.body = sp_body
            # print(sp.name)
            # for b in sp.body:
            #     print(b)

    def parse_procedures(self):
        self.procedures = []
        rep_alter_sp = 'alter\s+procedure\s+(\w+)'
        re_alter_sp = re.compile(rep_alter_sp, re.IGNORECASE)

        for statement in self.__statements[:]:
            m = re_alter_sp.match(statement)
            if m is not None:
                sp_name = m.group(1)
                sp = StoredProcedure(sp_name)
                sp.body.append(statement)
                self.procedures.append(sp)

    def parse_triggers(self):
        self.triggers = []
        rep_create_trigger = \
            'create\s+trigger\s+(?P<p_tr_name>\w+)\s+for\s+(?P<p_table_name>\w+)' \
            '(?:\s+(active|inactive))' \
            '(?P<p_tr_place>\s+(before|after)\s+(insert|update|delete))' \
            '(?:\s+position\s+(?P<p_tr_position>\d+))'
            #'(?:\s+active)(?P<p_tr_place>\s+(before|after)\s+(insert|update|delete))' \
            #'(?:\s+position\s+(?P<p_tr_position>\d+))as.*?;'
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

                tr = Trigger(tr_name)
                tr.table = table_name
                tr.place = tr_place
                tr.position = tr_pos
                tr.body.append(statement)

                self.triggers.append(tr)

    def overwrite_tr_bodies(self):
        term = ';'
        for tr in self.triggers:
            found = False
            tr_body = []
            for line in self.__lines[:]:
                if not found:
                    term = self.replace_term(line, term)
                    rep = 'create\s+trigger\s+{}'.format(tr.name)
                    m = re.match(rep, line, re.IGNORECASE)
                    if m is not None:
                        found = True
                if found:
                    tr_body.append(line.rstrip())
                    rep_end = "end\s*\\{}".format(term)
                    if re.match(rep_end, line, re.IGNORECASE):
                        found = False
                        break
                    if line.strip() == term:
                        found = False
                        break
            tr.body = tr_body
            # print(tr.name)
            # for b in tr.body:
            #     print(b)

    def parse_inserts(self):
        for statement in self.__statements[:]:
            if statement.lower().startswith('insert'):
                self.data.append(statement)

    def parse_header(self):
        for statement in self.__statements[:]:
            colon_count = statement.count(':')
            regexp_alias = \
                "create\s+database\s+\'(?P<p_db_name>.*)\'\s+" \
                "user\s+\'(?P<p_db_user>.*)\'\s+password\s+\'(?P<p_db_password>.*)\'"
            regexp_host = \
                "create\s+database\s+\'(?P<p_db_host>[\w\d\-_.]+):(?P<p_db_name>.+)\'\s+" \
                "user\s+\'(?P<p_db_user>.*)\'\s+password\s+\'(?P<p_db_password>.*)\'"
            regexp_map = {
                0: regexp_alias,
                1: regexp_host,
                2: regexp_host
            }
            regexp_pattern = regexp_alias
            if colon_count in regexp_map:
                regexp_pattern = regexp_map[colon_count]

            m = re.match(regexp_pattern, statement, re.IGNORECASE)
            if m is not None:
                groups = m.groupdict()
                if "p_db_host" in groups:
                    self.host = groups["p_db_host"].strip()
                    drive_list = ['a', 'b', 'c', 'd', 'e', 'f']
                    if self.host in drive_list:
                        self.host = ''
                else:
                    self.host = ''
                if "p_db_name" in groups:
                    self.alias = groups["p_db_name"].strip()
                    self.alias = os.path.basename(self.alias)
                    self.alias = path.splitext(self.alias)[0]
                else:
                    self.alias = ''
                if "p_db_user" in groups:
                    self.username = groups["p_db_user"].strip()
                else:
                    self.username = ''
                if "p_db_password" in groups:
                    self.password = groups["p_db_password"].strip()
                else:
                    self.password = ''


    def parse_statements(self):
        self.parse_header()
        self.parse_generators()
        self.parse_domains()
        self.parse_views()
        self.parse_tables()
        self.parse_procedures()
        self.parse_triggers()
        self.parse_inserts()

        # print(self.data)
        # print("h " + self.host)
        # print("a " + self.alias)
        # print(self.username)
        # print(self.password)


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
        for sp in self.procedures:
            print(sp.name)
        for tr in self.triggers:
            print(tr.name)
