#!/usr/bin/env python
# -*- coding: utf-8 -*-
# T O D O: сделать по образу и подобию pn_pgsql.py (PysdunMssql)
#
# This python script converts SQL-script writeen on Interbase/Firebird dialect
# to Microsoft Transact-SQL compatible script
# 
# Restrictions: 
#   - Don't use comma (;) char anywthere except statement delimiter (for example, in object descriptions)
#   - Use simple english database object names (without spaces, national characters, etc)
#   - Dont't use remote server connection string (like 192.168.47.38:/srv/firebird/moonhattan) in source script 
#
# 2013.03.14 [+] Check for "describe column", "comment on" statements
# 2013.03.13 [+] Timestamp column datatype changed to datetime for MSSQL
#                GETDATE() used instead of "NOW" Firebird function
# 2013.01.01 [+] Initial release, base objects supported (database creation, domains, tables)
#                Not yet support for views, stored procedures and triggers
#                
# 
#


import re
import codecs
import os

from os import path

import ibe_ddl


# PYSDUN - PYthon Schema/structure of Database UNificator
# Convert IbeSchema to Microsoft SQLServer script
class PysdunMssql:

    def __init__(self, schema):
        self.schema = schema

    @staticmethod
    def replace_data_type(data_type):
        blob_bin = 'varbinary(max)'
        blob_memo = 'varchar(max)'
        gr_sub_type = 'gr_sub_type'
        gr_segment_size = 'gr_segment_size'
        regex_blob = 'blob(?:\s+sub_type\s+(?P<{}>\d+))(?:\s+segment\s+size\s+(?P<{}>\d+))'.format(
            gr_sub_type, gr_segment_size
        )
        re_blob = re.compile(regex_blob, re.IGNORECASE)

        mdt = re_blob.match(data_type)
        if mdt:
            data_type = 'varchar(max)'
            # print(mdt.groupdict())
            if gr_sub_type in mdt.groupdict():
                sub_type = mdt.groupdict()[gr_sub_type]
                sub_types = {
                    '0': blob_bin,
                    '1': blob_memo
                }
                if sub_type in sub_types:
                    data_type = sub_types[sub_type]
                else:
                    data_type = blob_bin
                    
        # Тип данных timestamp - это синоним к типу данных rowversion и не предназначен для хранения даты и времени
        # поэтому недо заменить его на datetime (или datetime2), тем более что
        # GETDATE() в MSSQL работает только с полями типа datetime, с timestamp-полями - не работает

        data_type = re.sub('^[t_]timestamp', 'datetime', data_type, re.IGNORECASE)
        data_type = re.sub('numeric(18,\s*0)', 'int64', data_type, re.IGNORECASE)

        data_type = re.sub('^[t_]boolean', 'bit', data_type, re.IGNORECASE)

        data_type = re.sub('default\s+false', 'default 0', data_type, re.IGNORECASE)
        data_type = re.sub('default\s+true', 'default 1', data_type, re.IGNORECASE)

        data_type = re.sub("'now'", 'getdate()', data_type, re.IGNORECASE)

        return data_type

    def export(self, filename):
        filename_pair = path.splitext(filename)
        filename_file = filename_pair[0]
        filename_ext = filename_pair[1]

        lines = []
        #
        lines = []
        #
        sequences = set()
        for generator in self.schema.generators:
            sequence_name = generator.name
            sequences.add(sequence_name)
        #

        if self.schema.domains:
            for d in self.schema.domains:
                data_type = PysdunMssql.replace_data_type(d.data_type)

                domain_name = d.name
                lines.append('create type {0} from {1}'.format(domain_name, data_type))
        #
        for table_name in self.schema.tables:
            t = self.schema.tables[table_name]
            field_list = []
            for field in t.fields:
                serial = ''
                not_null = 'not null'
                default = ''
                data_type = self.replace_data_type(field.data_type)
                if field.nullable:
                    not_null = ""
                for d in self.schema.domains:
                    if field.data_type.lower() == d.name.lower():
                        if d.autoinc:
                            # serial = 'identity (1, 1)'
                            serial = 'identity'

                            # [i] for mssql-2012 and higher:
                            # for generator in self.schema.generators:
                            #     if generator.is_ownered_by(table_name, field.name):
                            #         serial = ''
                            #         default = "default next value for {}".format(generator.name)
                            #         break
                            # if serial != '':  # found default sequence
                            #     data_type = ''
                            #     not_null = ''
                        break
                field_item = '{} {} {} {} {}'.format(field.name, serial, data_type, not_null, default)
                field_item = ibe_ddl.strip_statement(field_item)

                field_list.append(field_item)
            template = 'create t {} ({})'
            table_statement = template.format(
                t.name,
                ', '.join([str(f) for f in field_list]))
            lines.append(table_statement)
        #
        for table_name in self.schema.tables:
            t = self.schema.tables[table_name]
            if t.uk is not None:
                for fk_name in t.uk:
                    field_list = t.uk[fk_name]
                    template = 'alter t {} add constraint {} unique ({})'
                    fk_statement = template.format(
                        table_name, fk_name,
                        ', '.join([str(f) for f in field_list]))
                    lines.append(fk_statement)
            if t.x is not None:
                for x_name in t.x:
                    field_list = t.x[x_name][0]
                    order = t.x[x_name][1]
                    unique = t.x[x_name][2]
                    if order is None:
                        order = ''
                    if unique is None:
                        unique = ''
                    index_statement = 'create {} index {} on {} ({})'.format(
                        unique, x_name, table_name,
                        ', '.join([str(f + ' ' + order) for f in field_list]))
                    index_statement = ibe_ddl.strip_statement(index_statement)
                    lines.append(index_statement)
            if t.pk is not None:
                pk_name = 'pk_{}'.format(table_name)
                template = 'alter t {} add constraint {} primary key ({})'
                pk_statement = template.format(
                    table_name, pk_name,
                    ', '.join([str(f) for f in t.pk]))
                lines.append(pk_statement)
        #
        for table_name in self.schema.tables:
            t = self.schema.tables[table_name]
            if t.fk is not None:
                for fk_name in t.fk:
                    field_list = t.fk[fk_name][0]
                    ref_table_name = t.fk[fk_name][1]
                    ref_field_list = t.fk[fk_name][2]
                    del_rule = t.fk[fk_name][3]
                    upd_rule = t.fk[fk_name][4]
                    if del_rule is None:
                        del_rule = ""
                        # print('WARNING! NO ACTION! (' + fk_name + ':' + upd_rule + ')')
                        # upd_rule = "on update no action"
                    if upd_rule is None:
                        upd_rule = ""
                        # print('WARNING! NO ACTION! (' + fk_name + ':' + del_rule + ')')
                        # del_rule = "on delete no action"
                    if del_rule:
                        del_rule = del_rule.strip()
                    if upd_rule:
                        upd_rule = upd_rule.strip()
                    template = 'alter t {} add constraint {} foreign key ({}) references {} ({}) {} {}'
                    fk_statement = template.format(
                        table_name, fk_name,
                        ', '.join([str(f) for f in field_list]),
                        ref_table_name,
                        ', '.join([str(f) for f in ref_field_list]), del_rule, upd_rule)
                    fk_statement = ibe_ddl.strip_statement(fk_statement)
                    # dfpost patch
                    # fk_statement = fk_statement.replace('alter t navig', '-- alter t navig')
                    # fk_statement = fk_statement.replace('alter t pf_result', '-- alter t pf_result')
                    # fk_statement = fk_statement.replace('alter t worksession', '-- alter t worksession')
                    lines.append(fk_statement)
        #
        for view in self.schema.views:
            lines.append(view)

        prescript = []

        if not self.schema.host:
            self.schema.host = '127.0.0.1'

        go = '\ngo\n\n'

        # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
        data_path = "C:\\Program Files\\Microsoft SQL Server\\MSSQL11.MSSQLSERVER\\MSSQL\\DATA"

        #
        # use [master]
        # go
        # declare @data_path varchar(max) = '';
        # select @data_path = substring(physical_name, 1, charindex(N'master.mdf', lower(physical_name)) - 1)
        # from master.sys.master_files
        # where database_id = 1 and file_id = 1
        # print @data_path
        # go
        #

        prescript.append("use [master]")
        # cdb.append("if exists(select * from sys.databases where name = '{0}') drop database {0}".format(database))
        prescript.append("if exists(select * from sys.databases where name = '{0}')".format(self.schema.alias))
        prescript.append("begin")
        prescript.append("  print 'Database {0} exists'".format(self.schema.alias))
        prescript.append("  alter database {0} set offline with rollback immediate".format(self.schema.alias))
        prescript.append("  alter database {0} set online".format(self.schema.alias))
        prescript.append("  drop database {0}".format(self.schema.alias))
        prescript.append("end")
        prescript.append("else")
        prescript.append("begin")
        prescript.append("  print 'Database {0} does not exists'".format(self.schema.alias))
        prescript.append("end")

        prescript.append("create database [{0}]".format(self.schema.alias, data_path))
        prescript.append("go")

        prescript.append("alter database [{0}] collate Cyrillic_General_CI_AS".format(self.schema.alias))
        prescript.append("go")

        prescript.append("use [{0}]".format(self.schema.alias))

        file_encoding_utf8 = 'utf-8'
        file_encoding_win1251 = 'cp1251'
        # pgsql_encoding_utf8 = 'UTF8'
        # pgsql_encoding_win1251 = 'WIN1251'
        # pg_encoding = {
        #     file_encoding_utf8: pgsql_encoding_utf8,
        #     file_encoding_win1251: pgsql_encoding_win1251
        # }
        file_encoding = file_encoding_win1251
        # pgsql_encoding = pg_encoding[file_encoding]
        f = codecs.open(filename, 'w', encoding=file_encoding)
        # f = open(filename, 'w')
        try:
            f.write('-- {} \n'.format(file_encoding))
            # f.write("set client_encoding to '{}';\n".format(pgsql_encoding))
            for item in prescript[:]:
                f.write(item + ';')

            for item in lines:
                value = item
                f.write(value + ';')
                f.write(go)
            f.write('/* --- */\n')
            for item in self.schema.data:
                f.write(item + '\n')
            f.write(go)
            f.write('/* EOF */\n')
        finally:
            f.close()

        #
        #
        #
        #
        filename = filename_file + '-triggers' + filename_ext

        if os.path.isfile(filename):
            filename += '~'
        if os.path.isfile(filename):
            os.remove(filename)

        lines = []

        for tr in self.schema.triggers:
            body_mark = '$body$'
            trigger_procedure = 'trf_{}'.format(tr.name)
            lines.append('/* - - - - - - - - - - - - - - - - */')
            lines.append('create or replace function {}()'.format(trigger_procedure))
            lines.append('  returns opaque as')
            lines.append(body_mark)
            lines.append('-- / *')

            for b in tr.body:
                lines.append('-- ' + b)

            lines.append('-- * /')
            lines.append(body_mark)
            lines.append("language 'plpgsql'")
            lines.append(';')

            lines.append('/* - - - - */')
            lines.append('create trigger {}'.format(tr.name))
            lines.append('{}'.format(tr.place))
            lines.append('on {}'.format(tr.table))
            lines.append('for each row execute procedure {}'.format(trigger_procedure))
            lines.append(';')

        f = open(filename, 'w')
        try:
            for item in prescript:
                f.write(item + ';\n')
            for item in lines:
                f.write(item + '\n')
            # for item in ins:
            #     f.write(item + ';\n')
            f.write('/* EOF */\n')
        finally:
            f.close()

        #
        for sp in self.schema.procedures:
            lines = []
            lines.append('/* - - - - - - - - - - - - - - - - */')
            lines.append('/*')
            for b in sp.body:
                lines.append('-- ' + b)
            lines.append('*/')
            lines.append(';')

            filename = filename_file + '-sp-' + sp.name + filename_ext

            if os.path.isfile(filename):
                filename += '~'
            if os.path.isfile(filename):
                os.remove(filename)

            f = open(filename, 'w')
            try:
                # for item in prescript:
                #     f.write(item + ';\n')
                for item in lines:
                    f.write(item + '\n')
                # for item in ins:
                #     f.write(item + ';\n')
                f.write('/* EOF */\n')
            finally:
                f.close()


  #for statement in statements:
  #  print(statement)
  #print('')
  
  
  
if __name__ == "__main__":
  main(sys.argv[1:])
